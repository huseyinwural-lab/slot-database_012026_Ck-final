# Bot Registry (Config & Hardening)

Bu doküman, config ve hardening ile ilgili test botlarının/süreçlerinin iskelet tanımını içerir.

- `config-regression-bot`
  - enabled: true
  - runs: basic GET/POST/GET round-trip & diff on canonical test games
  - scope: Slot/Crash/Dice/Blackjack/Poker için temel konfigürasyon ve diff doğrulamaları

- `hardening-bot`
  - enabled: false
  - runs: suites/jackpots_edge_cases, blackjack_limits_edge_cases, poker_rake_edge_cases
  - scope: `hardening_suites.yaml` içinde tanımlı edge case senaryolarını koşturur (kapalı başlar, ihtiyaç halinde açılır)

- `ui-e2e-bot`
  - enabled: true
  - runs: core UI flows for Slot/Crash/Dice/Blackjack/Poker (GameManagement, GameConfigPanel, diff UI, temel oyuncu akışları)
  - scope: Frontend/E2E akışların Playwright/agent tabanlı otomasyonu

- `game-robot`
  - enabled: true
  - type: "deterministic_mvp"
  - description: "Canonical Slot/Crash/Dice test oyunları üzerinde belirli sayıda round için deterministic config round-trip çalıştırır."
  - command: "python -m backend.app.bots.game_robot --game-types slot,crash,dice --rounds 50"
