# Test Game Inventory Matrix (P0-D)

Bu dosya, sistemdeki canonical test oyunlarını ve çekirdek oyun tiplerini (core_type) özetler.

## Core Types

Mevcut core_type listesi (DB'den):

- CRASH
- DICE
- REEL_LINES
- SLOT
- TABLE_BLACKJACK
- TABLE_POKER

## Canonical / Önemli Oyunlar Tablosu

Not: currency alanı oyun kayıtlarında tutulmadığı için `N/A` olarak işaretlenmiştir; environment, `tenant_id` alanından türetilmiştir.

| Game Name                                   | Game ID                                 | core_type       | currency | environment     | is_test | tags                     |
|--------------------------------------------|-----------------------------------------|-----------------|----------|-----------------|---------|--------------------------|
| Test Slot Game                             | f9596f63-a1f6-411b-aec4-f713b900894e   | SLOT            | N/A      | default         | false   |                          |
| **Test Slot Game (QA)**                    | f78ddf21-c759-4b8c-a5fb-28c90b3645ab   | SLOT            | N/A      | default_casino  | true    | qa,slot                  |
| **Test Crash Game (Advanced Safety QA)**   | 52ba0d07-58ab-43c1-8c6d-8a3b2675a7a8   | CRASH           | N/A      | default_casino  | true    | qa,advanced_safety       |
| Test Crash Game                            | 382ac044-9378-4ee2-bfd0-f50377e7ee04   | CRASH           | N/A      | default_casino  | false   |                          |
| **Test Dice Game (Advanced Limits QA)**    | 137e8fbf-3f41-4407-b9a5-41efdd0dc78c   | DICE            | N/A      | default_casino  | true    | qa,advanced_limits       |
| Test Dice Game (Advanced Limits QA)        | 5f26b930-8256-4f78-82e5-304c73a1f38f   | DICE            | N/A      | default_casino  | true    | qa,advanced_limits       |
| Test Dice Game                             | 4483adea-1629-4a01-99e9-095a701b6ff8   | DICE            | N/A      | default_casino  | false   |                          |
| **Test Reel Lines Game (Config QA)**       | 1c75a140-c6a1-42eb-9394-ec5293f4ab4a   | REEL_LINES      | N/A      | default_casino  | true    | qa,canonical,reel_lines  |
| Test Manual Slot                           | 7ddc2560-9655-46f3-9cc5-072ddcbd27dd   | REEL_LINES      | N/A      | default_casino  | false   |                          |
| **Test Blackjack Game (Config QA)**        | c533cd14-2ba4-425e-8213-3ea69f55ba7f   | TABLE_BLACKJACK | N/A      | default_casino  | true    | qa,canonical,blackjack   |
| Test Blackjack Table                       | test_blackjack_1765382929              | TABLE_BLACKJACK | N/A      | default_casino  | false   |                          |
| Test Blackjack Table                       | test_blackjack_1765382935              | TABLE_BLACKJACK | N/A      | default_casino  | false   |                          |
| Test Blackjack VIP Table                   | 95765f72-f673-4e75-bfa7-97d78b152f56   | TABLE_BLACKJACK | N/A      | default_casino  | false   |                          |
| **Test Poker Game (Config QA)**            | 6280959b-5dad-40be-8cd0-8a41d721d261   | TABLE_POKER     | N/A      | default_casino  | true    | qa,canonical,poker       |
| Texas Hold'em Cash Game (VIP Edition ...)  | bd8654bc-2253-40c5-ba2f-edde2ca76830   | TABLE_POKER     | N/A      | default         | false   | VIP                      |

> Not: DB'de çok sayıda ek "Test Slot Game" ve benzeri varyant bulunmaktadır; burada P0-D kapsamında referans alınacak canonical/önemli örnekler tabloya işlenmiştir.

## Canonical Status Özeti

Aşağıda her core_type için en az bir "canonical" test oyununun varlığı özetlenmiştir.

- **SLOT**: VAR → `Test Slot Game (QA)` (id=f78ddf21-..., is_test=true, tags=[qa,slot])
- **CRASH**: VAR → `Test Crash Game (Advanced Safety QA)` (id=52ba0d07-..., is_test=true, tags=[qa,advanced_safety])
- **DICE**: VAR → `Test Dice Game (Advanced Limits QA)` (id=137e8fbf-..., is_test=true, tags=[qa,advanced_limits])
- **REEL_LINES**: VAR → `Test Reel Lines Game (Config QA)` (id=1c75a140-..., is_test=true, tags=[qa,canonical,reel_lines])
- **TABLE_BLACKJACK**: VAR → `Test Blackjack Game (Config QA)` (id=c533cd14-..., is_test=true, tags=[qa,canonical,blackjack])
- **TABLE_POKER**: VAR → `Test Poker Game (Config QA)` (id=6280959b-..., is_test=true, tags=[qa,canonical,poker])

### canonical_present

- SLOT
- CRASH
- DICE
- REEL_LINES
- TABLE_BLACKJACK
- TABLE_POKER

### canonical_missing

- _(boş – tüm mevcut core_type'lar için en az bir canonical test game tanımlı)_

## Test Game Config Coverage (P0-D)

| Game Name                             | core_type       | Config Type            | Status | Notlar                                                |
|---------------------------------------|-----------------|------------------------|--------|-------------------------------------------------------|
| Test Slot Game (QA)                   | SLOT            | Slot Advanced          | PRO    | pozitif + negatif validation (autoplay range)        |
| Test Slot Game (QA)                   | SLOT            | Paytable/Reels/JP      | PRO    | P0-B/P0-C senaryoları (override, manual reels, JP)   |
| Test Crash Game (Advanced Safety QA)  | CRASH           | Crash Advanced         | PRO    | limits + enforcement + country overrides             |
| Test Dice Game (Advanced Limits QA)   | DICE            | Dice Advanced          | PRO    | limits + enforcement + country overrides             |
| Test Reel Lines Game (Config QA)      | REEL_LINES      | Reel Strips/Paytable/JP| PRO    | pozitif round-trip + Mini JP (API, UI henüz yok)     |
| Test Blackjack Game (Config QA)       | TABLE_BLACKJACK | BlackjackRules         | PRO    | baseline QA + BLACKJACK_RULES_VALIDATION_FAILED testi|
| Test Poker Game (Config QA)           | TABLE_POKER     | PokerRules             | PRO    | baseline QA + POKER_RULES_VALIDATION_FAILED testi    |

## Test Game History & Diff Readiness (P0-D)

| Game Name                        | core_type       | Config Type           | History | Diff Support     | Notlar                                                      |
|----------------------------------|-----------------|-----------------------|---------|------------------|-------------------------------------------------------------|
| Test Slot Game (QA)              | SLOT            | Slot Adv/Pay/Reels/JP | VAR     | VAR (backend+UI) | P0-B/C senaryoları; slot-advanced/paytable/reels/JP diff   |
| Test Reel Lines Game (Config QA) | REEL_LINES      | Paytable/Reels/JP     | VAR     | VAR (backend)    | Reels: reels[2][5] WILD removed; Paytable: lines 20→25; JP: contribution 1.5→2.0 |
| Test Blackjack Game (Config QA)  | TABLE_BLACKJACK | BlackjackRules        | VAR     | YOK (future)     | >=2 versiyon; history dolu; diff API future scope          |
| Test Poker Game (Config QA)      | TABLE_POKER     | PokerRules            | VAR     | YOK (future)     | >=2 versiyon; history dolu; diff API future scope          |

## P0-D Summary

P0-D kapsamında tüm mevcut core_type'lar için canonical test oyunlar tanımlanmış, temel config coverage PRO seviyeye çekilmiş ve history & diff readiness tablosu ile dokümante edilmiştir. Blackjack/Poker diff API sonraki fazda (P1: Hardening) ele alınacaktır.
