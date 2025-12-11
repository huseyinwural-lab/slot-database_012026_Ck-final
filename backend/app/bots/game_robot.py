import os
import sys
import time
from dataclasses import dataclass
from typing import List, Dict, Any, Optional

import httpx


# --- Sabitler (manuel güncellenebilir) ---
DEFAULT_ROUNDS = 50

TEST_SLOT_ID = "f78ddf21-c759-4b8c-a5fb-28c90b3645ab"  # Test Slot Game (QA)
TEST_CRASH_ID = "52ba0d07-58ab-43c1-8c6d-8a3b2675a7a8"  # Test Crash Game (Advanced Safety QA)
TEST_DICE_ID = "137e8fbf-3f41-4407-b9a5-41efdd0dc78c"  # Test Dice Game (Advanced Limits QA)

SLOT_BET_AMOUNT = 1.0
CRASH_BETS = [1.0, 2.0]
DICE_BETS = [1.0, 5.0]
DICE_CHANCES = [50.0, 75.0]  # yüzde olarak

# Backend base URL - env'den okunur, yoksa localhost fallback
BASE_URL = os.getenv("GAME_ROBOT_BASE_URL", "http://localhost:8001")


@dataclass
class ScenarioResult:
    game_type: str
    rounds: int
    success_count: int
    errors: List[Dict[str, Any]]

    @property
    def has_errors(self) -> bool:
        return len(self.errors) > 0


class HttpClient:
    def __init__(self, base_url: str, tenant_id: str, api_key: Optional[str] = None, timeout: float = 10.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.tenant_id = tenant_id
        self.api_key = api_key

    def _full_url(self, path: str) -> str:
        if not path.startswith("/"):
            path = "/" + path
        return f"{self.base_url}{path}"

    def _headers(self) -> Dict[str, str]:
        headers = {
            "X-Tenant-ID": self.tenant_id,
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def get(self, path: str, params: Optional[Dict[str, Any]] = None) -> httpx.Response:
        url = self._full_url(path)
        return httpx.get(url, params=params, headers=self._headers(), timeout=self.timeout)

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

    parser = argparse.ArgumentParser(description="Deterministic Game Robot (Slot/Crash/Dice)")
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
        help=f"Her oyun tipi için tur sayısı (varsayılan: {DEFAULT_ROUNDS})",
    )

    args = parser.parse_args(argv)

    game_types = [g.strip().lower() for g in args.game_types.split(",") if g.strip()]
    valid = {"slot", "crash", "dice"}
    for g in game_types:
        if g not in valid:
            raise SystemExit(f"Geçersiz game-type: {g}. Desteklenenler: slot,crash,dice")

    return {"game_types": game_types, "rounds": args.rounds}


def main(argv: Optional[List[str]] = None) -> int:
    if argv is None:
        argv = sys.argv[1:]

    try:
        parsed = parse_args(argv)
    except SystemExit as e:
        # argparse zaten mesajı bastı
        return int(e.code) if isinstance(e.code, int) else 1

    client = HttpClient(BASE_URL)
    game_types: List[str] = parsed["game_types"]
    rounds: int = parsed["rounds"]

    print(f"[GameRobot] BASE_URL={BASE_URL} | game_types={game_types} | rounds={rounds}")

    results: List[ScenarioResult] = []

    if "slot" in game_types:
        print("[GameRobot] SLOT senaryosu başlıyor...")
        results.append(run_slot_scenario(client, rounds))

    if "crash" in game_types:
        print("[GameRobot] CRASH senaryosu başlıyor...")
        results.append(run_crash_scenario(client, rounds))

    if "dice" in game_types:
        print("[GameRobot] DICE senaryosu başlıyor...")
        results.append(run_dice_scenario(client, rounds))

    total_errors = 0
    for res in results:
        err_count = len(res.errors)
        total_errors += err_count
        status = "OK" if err_count == 0 else "FAIL"
        print(f"[{res.game_type.upper()}] {status} ({res.success_count}/{res.rounds}) - errors={err_count}")
        if err_count > 0:
            print(f"  İlk birkaç hata (en fazla 3):")
            for e in res.errors[:3]:
                print(f"    round={e.get('round')} status={e.get('status')} body={e.get('body')}")

    if total_errors == 0:
        print("[GameRobot] Tüm senaryolar başarıyla tamamlandı.")
        return 0
    else:
        print(f"[GameRobot] Toplam hata sayısı: {total_errors}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
