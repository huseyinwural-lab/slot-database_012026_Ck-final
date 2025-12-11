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
| Test Manual Slot                           | 7ddc2560-9655-46f3-9cc5-072ddcbd27dd   | REEL_LINES      | N/A      | default_casino  | false   |                          |
| Test Manual Slot                           | ae0a4c65-aeca-48a2-9a05-e1d0d8eadc55   | REEL_LINES      | N/A      | default_casino  | false   |                          |
| Test Manual Slot                           | b09e9e77-e23f-4f33-9a63-a6426441e8a1   | REEL_LINES      | N/A      | default_casino  | false   |                          |
| Test Blackjack Table                       | test_blackjack_1765382929              | TABLE_BLACKJACK | N/A      | default_casino  | false   |                          |
| Test Blackjack Table                       | test_blackjack_1765382935              | TABLE_BLACKJACK | N/A      | default_casino  | false   |                          |
| Test Blackjack VIP Table                   | 95765f72-f673-4e75-bfa7-97d78b152f56   | TABLE_BLACKJACK | N/A      | default_casino  | false   |                          |
| Texas Hold'em Cash Game (VIP Edition ...)  | bd8654bc-2253-40c5-ba2f-edde2ca76830   | TABLE_POKER     | N/A      | default         | false   | VIP                      |

> Not: Bu tablo şu an canonical/önemli oyun örneklerini listeliyor; DB'de çok sayıda ek "Test Slot Game" varyantı ve başka test oyunlar da mevcut. Gerekirse bu dosya ileride tam envanteri içerecek şekilde genişletilebilir.

## Canonical Status Özeti

Aşağıda her core_type için en az bir "canonical" test oyununun varlığı özetlenmiştir.

- **SLOT**: VAR → `Test Slot Game (QA)` (id=f78ddf21-..., is_test=true, tags=[qa,slot])
- **CRASH**: VAR → `Test Crash Game (Advanced Safety QA)` (id=52ba0d07-..., is_test=true, tags=[qa,advanced_safety])
- **DICE**: VAR → `Test Dice Game (Advanced Limits QA)` (id=137e8fbf-..., is_test=true, tags=[qa,advanced_limits])
- **REEL_LINES**: YOK (sadece `Test Manual Slot` kayıtları var, is_test=false, tags boş)
- **TABLE_BLACKJACK**: YOK (birden fazla `Test Blackjack Table` ve `Test Blackjack VIP Table` var, fakat is_test=false, tags boş)
- **TABLE_POKER**: YOK (sadece VIP masa: `Texas Hold'em Cash Game (VIP Edition ...)`, is_test=false, tag=VIP)

### canonical_present

- SLOT
- CRASH
- DICE

### canonical_missing

- REEL_LINES
- TABLE_BLACKJACK
- TABLE_POKER

Bu liste P0-D'nin bir sonraki adımlarında eksik canonical test oyunlarının yaratılması için kullanılacaktır.
