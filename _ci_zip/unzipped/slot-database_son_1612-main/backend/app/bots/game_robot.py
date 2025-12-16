import os
import sys
import time
from dataclasses import dataclass
from typing import List, Dict, Any, Optional

import httpx


@dataclass
class ScenarioResult:
    game_type: str
    rounds: int
    success_count: int
    errors: List[Dict[str, Any]]


# --- Sabitler (manuel güncellenebilir) ---
DEFAULT_ROUNDS = 50

# Backend base URL - env'den okunur, yoksa preview panel URL'sine benzer bir default
BASE_URL = os.getenv("GAME_ROBOT_BASE_URL", "http://localhost:8001")

# Test game IDs
TEST_SLOT_ID = "test-slot-game"
TEST_CRASH_ID = "test-crash-game"
TEST_DICE_ID = "test-dice-game"

# Test bet amounts and parameters
CRASH_BETS = [10, 25, 50, 100, 200]
DICE_BETS = [5, 15, 30, 75, 150]
DICE_CHANCES = [50.0, 25.0, 75.0, 10.0, 90.0]


class HttpClient:
    def __init__(self, base_url: str, api_key: str, timeout: float = 10.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.api_key = api_key

    def _full_url(self, path: str) -> str:
        if not path.startswith("/"):
            path = "/" + path
        return f"{self.base_url}{path}"

    def _headers(self) -> Dict[str, str]:
        headers: Dict[str, str] = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def get(self, path: str) -> httpx.Response:
        url = self._full_url(path)
        return httpx.get(url, headers=self._headers(), timeout=self.timeout)

    def post(self, path: str, json: Optional[Dict[str, Any]] = None) -> httpx.Response:
        url = self._full_url(path)
        return httpx.post(url, json=json, headers=self._headers(), timeout=self.timeout)


def run_slot_scenario(client: HttpClient, rounds: int) -> ScenarioResult:
    errors: List[Dict[str, Any]] = []
    success = 0

    # Varsayılan: slot için doğrudan bir "spin" endpoint'i yok, bu yüzden
    # mevcut math/config endpointlerine basit bir sağlık kontrolü yapıyoruz.
    # Eğer ileride gerçek play endpoint'i eklenirse, burada değiştirilebilir.
    for i in range(rounds):
        resp = client.get(f"/api/v1/games/{TEST_SLOT_ID}/config/slot-advanced")
        if 200 <= resp.status_code < 300:
            success += 1
        else:
            try:
                data = resp.json()
            except Exception:
                data = {"raw": resp.text}
            errors.append({
                "round": i + 1,
                "status": resp.status_code,
                "body": data,
            })
        time.sleep(0.01)

    return ScenarioResult(game_type="slot", rounds=rounds, success_count=success, errors=errors)


def run_crash_scenario(client: HttpClient, rounds: int) -> ScenarioResult:
    errors: List[Dict[str, Any]] = []
    success = 0

    # Bu MVP'de gerçek bir "play crash" endpoint'i henüz tanımlı olmadığı için,
    # crash-math config endpoint'ine GET/POST round-trip ile basit bir sağlık
    # kontrolü yapıyoruz. İleride gerçek play endpoint'i eklendiğinde burası
    # kolayca değiştirilebilir.

    # Önce mevcut config'i okuyalım
    base_resp = client.get(f"/api/v1/games/{TEST_CRASH_ID}/config/crash-math")
    if not (200 <= base_resp.status_code < 300):
        try:
            data = base_resp.json()
        except Exception:
            data = {"raw": base_resp.text}
        errors.append({
            "round": 0,
            "status": base_resp.status_code,
            "body": data,
        })
        return ScenarioResult(game_type="crash", rounds=0, success_count=0, errors=errors)

    base_cfg = base_resp.json()

    for i in range(rounds):
        bet = CRASH_BETS[i % len(CRASH_BETS)]
        payload = {
            # zorunlu alanları mevcut config'ten kopyala
            "base_rtp": base_cfg.get("base_rtp", 96.0),
            "volatility_profile": base_cfg.get("volatility_profile", "medium"),
            "min_multiplier": base_cfg.get("min_multiplier", 1.0),
            "max_multiplier": base_cfg.get("max_multiplier", 500.0),
            "max_auto_cashout": base_cfg.get("max_auto_cashout", 100.0),
            "round_duration_seconds": base_cfg.get("round_duration_seconds", 12),
            "bet_phase_seconds": base_cfg.get("bet_phase_seconds", 6),
            "grace_period_seconds": base_cfg.get("grace_period_seconds", 2),
            "min_bet_per_round": bet,
            "max_bet_per_round": max(bet * 10, base_cfg.get("max_bet_per_round") or 0),
            "max_loss_per_round": base_cfg.get("max_loss_per_round"),
            "max_win_per_round": base_cfg.get("max_win_per_round"),
            "max_rounds_per_session": base_cfg.get("max_rounds_per_session"),
            "max_total_loss_per_session": base_cfg.get("max_total_loss_per_session"),
            "max_total_win_per_session": base_cfg.get("max_total_win_per_session"),
            "enforcement_mode": base_cfg.get("enforcement_mode", "log_only"),
            "country_overrides": base_cfg.get("country_overrides"),
            "provably_fair_enabled": base_cfg.get("provably_fair_enabled", True),
            "rng_algorithm": base_cfg.get("rng_algorithm", "sha256_chain"),
            "seed_rotation_interval_rounds": base_cfg.get("seed_rotation_interval_rounds"),
            "summary": f"robot_round_{i+1}",
        }

        resp = client.post(f"/api/v1/games/{TEST_CRASH_ID}/config/crash-math", json=payload)
        if 200 <= resp.status_code < 300:
            success += 1
        else:
            try:
                data = resp.json()
            except Exception:
                data = {"raw": resp.text}
            errors.append({
                "round": i + 1,
                "status": resp.status_code,
                "body": data,
            })
        time.sleep(0.01)

    return ScenarioResult(game_type="crash", rounds=rounds, success_count=success, errors=errors)


def run_dice_scenario(client: HttpClient, rounds: int) -> ScenarioResult:
    errors: List[Dict[str, Any]] = []
    success = 0

    # Dice için de dice-math config endpoint'ine GET/POST round-trip ile
    # deterministic bir sağlık kontrolü yapıyoruz.

    base_resp = client.get(f"/api/v1/games/{TEST_DICE_ID}/config/dice-math")
    if not (200 <= base_resp.status_code < 300):
        try:
            data = base_resp.json()
        except Exception:
            data = {"raw": base_resp.text}
        errors.append({
            "round": 0,
            "status": base_resp.status_code,
            "body": data,
        })
        return ScenarioResult(game_type="dice", rounds=0, success_count=0, errors=errors)

    base_cfg = base_resp.json()

    for i in range(rounds):
        bet = DICE_BETS[i % len(DICE_BETS)]
        chance = DICE_CHANCES[i % len(DICE_CHANCES)]

        payload = {
            "range_min": base_cfg.get("range_min", 0.0),
            "range_max": base_cfg.get("range_max", 99.99),
            "step": base_cfg.get("step", 0.01),
            "house_edge_percent": base_cfg.get("house_edge_percent", 1.0),
            "min_payout_multiplier": base_cfg.get("min_payout_multiplier", 1.01),
            "max_payout_multiplier": base_cfg.get("max_payout_multiplier", 990.0),
            "allow_over": base_cfg.get("allow_over", True),
            "allow_under": base_cfg.get("allow_under", True),
            "min_target": base_cfg.get("min_target", 1.0),
            "max_target": base_cfg.get("max_target", 98.0),
            "round_duration_seconds": base_cfg.get("round_duration_seconds", 5),
            "bet_phase_seconds": base_cfg.get("bet_phase_seconds", 3),
            "max_win_per_bet": max(bet * 10, base_cfg.get("max_win_per_bet") or 0),
            "max_loss_per_bet": max(bet * 2, base_cfg.get("max_loss_per_bet") or 0),
            "max_session_loss": base_cfg.get("max_session_loss"),
            "max_session_bets": base_cfg.get("max_session_bets"),
            "enforcement_mode": base_cfg.get("enforcement_mode", "log_only"),
            "country_overrides": base_cfg.get("country_overrides"),
            "provably_fair_enabled": base_cfg.get("provably_fair_enabled", True),
            "rng_algorithm": base_cfg.get("rng_algorithm", "sha256_chain"),
            "seed_rotation_interval_rounds": base_cfg.get("seed_rotation_interval_rounds"),
            "summary": f"robot_round_{i+1}_chance_{chance}",
        }

        resp = client.post(f"/api/v1/games/{TEST_DICE_ID}/config/dice-math", json=payload)
        if 200 <= resp.status_code < 300:
            success += 1
        else:
            try:
                data = resp.json()
            except Exception:
                data = {"raw": resp.text}
            errors.append({
                "round": i + 1,
                "status": resp.status_code,
                "body": data,
            })
        time.sleep(0.01)

    return ScenarioResult(game_type="dice", rounds=rounds, success_count=success, errors=errors)


def parse_args(argv: List[str]) -> Dict[str, Any]:
    import argparse

    parser = argparse.ArgumentParser(description="Casino Game Robot - Thin CLI (calls /api/v1/robot/round)")
    parser.add_argument(
        "--game-types",
        type=str,
        default="slot,crash,dice",
        help="Virgülle ayrılmış oyun tipleri: slot,crash,dice",
    )
    parser.add_argument(
        "--rounds",
        type=int,
        default=DEFAULT_ROUNDS,
        help=f"Toplam tur sayısı (varsayılan: {DEFAULT_ROUNDS})",
    )
    parser.add_argument(
        "--tenant-id",
        type=str,
        default="default_casino",
        help="Tenant ID (örn. default_casino, demo_renter) - sadece log amaçlı, asıl tenant API key'ten gelir",
    )
    parser.add_argument(
        "--api-key",
        type=str,
        required=True,
        help="ZORUNLU API key (Authorization: Bearer ...)",
    )
    parser.add_argument(
        "--base-url",
        type=str,
        default=BASE_URL,
        help="Backend base URL (örn. https://panel.domain.com)",
    )

    args = parser.parse_args(argv)

    game_types = [g.strip().lower() for g in args.game_types.split(",") if g.strip()]
    valid = {"slot", "crash", "dice"}
    for g in game_types:
        if g not in valid:
            raise SystemExit(f"Geçersiz game-type: {g}. Desteklenenler: slot,crash,dice")

    return {
        "game_types": game_types,
        "rounds": args.rounds,
        "tenant_id": args.tenant_id,
        "api_key": args.api_key,
        "base_url": args.base_url,
    }


def main(argv: Optional[List[str]] = None) -> int:
    if argv is None:
        argv = sys.argv[1:]

    try:
        parsed = parse_args(argv)
    except SystemExit as e:
        # argparse zaten mesajı bastı
        return int(e.code) if isinstance(e.code, int) else 1

    tenant_id: str = parsed["tenant_id"]
    api_key: Optional[str] = parsed["api_key"]
    base_url: str = parsed["base_url"]

    game_types: List[str] = parsed["game_types"]
    rounds: int = parsed["rounds"]

    client = HttpClient(base_url, api_key=api_key)

    print(
        f"[GameRobot] BASE_URL={base_url} | tenant_id={tenant_id} | game_types={game_types} | rounds={rounds}"
    )

    payload = {
        "game_types": game_types,
        "rounds": rounds,
        "tenant_id": tenant_id,
    }

    try:
        response = client.post("/api/v1/robot/round", json=payload)
    except Exception as exc:
        print(f"[GameRobot][ERROR] HTTP request failed: {exc}", file=sys.stderr)
        return 1

    if response.status_code == 401:
        print("[GameRobot][ERROR] Unauthorized (401) - API key geçersiz veya eksik", file=sys.stderr)
        return 1
    if response.status_code == 403:
        print("[GameRobot][ERROR] Forbidden (403) - Yetki veya scope yetersiz", file=sys.stderr)
        print(response.text, file=sys.stderr)
        return 1
    if response.status_code == 400:
        print("[GameRobot][ERROR] Bad Request (400) - Payload veya limit hatası", file=sys.stderr)
        print(response.text, file=sys.stderr)
        return 1
    if not (200 <= response.status_code < 300):
        print(f"[GameRobot][ERROR] Unexpected status code: {response.status_code}", file=sys.stderr)
        print(response.text, file=sys.stderr)
        return 1

    try:
        data = response.json()
    except Exception:
        print("[GameRobot][ERROR] Response JSON parse edilemedi", file=sys.stderr)
        print(response.text, file=sys.stderr)
        return 1

    results = data.get("results", [])
    total_rounds = data.get("total_rounds")
    tenant_id_from_api = data.get("tenant_id")

    print(
        f"[Robot] tenant={tenant_id_from_api} | rounds={total_rounds} | game_types={','.join(game_types)}"
    )

    for res in results:
        gt = res.get("game_type")
        r = res.get("rounds")
        errors = res.get("errors")
        avg_rtp = res.get("avg_rtp")
        avg_ms = res.get("avg_duration_ms")
        print(
            f"[Robot][{gt}] rounds={r} | errors={errors} | avg_rtp={avg_rtp} | avg_ms={avg_ms}"
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
