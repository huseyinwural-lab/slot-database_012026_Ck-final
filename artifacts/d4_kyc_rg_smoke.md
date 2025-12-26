# KYC & RG Smoke Test

- ERROR: (sqlite3.IntegrityError) NOT NULL constraint failed: player.wagering_requirement
[SQL: 
                INSERT INTO player (id, tenant_id, username, email, password_hash, balance_real_available, balance_real, balance_bonus, status, kyc_status)
                VALUES (?, ?, ?, ?, 'hash', 0, 0, 0, 'active', 'pending')
            ]
[parameters: ('76d852b4-85f7-40bd-876a-e22b686d910d', 'default_casino', 'smoke_781261d4', 'smoke_781261d4@test.com')]
(Background on this error at: https://sqlalche.me/e/20/gkpj)