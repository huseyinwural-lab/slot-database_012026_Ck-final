# KYC & RG Smoke Test

- ERROR: (sqlite3.IntegrityError) NOT NULL constraint failed: player.balance_real
[SQL: 
                INSERT INTO player (id, tenant_id, username, email, password_hash, balance_real_available, status, kyc_status)
                VALUES (?, ?, ?, ?, 'hash', 0, 'active', 'pending')
            ]
[parameters: ('46aa4ffb-9c43-4257-9785-ab13481f9d94', 'default_casino', 'smoke_ee33714a', 'smoke_ee33714a@test.com')]
(Background on this error at: https://sqlalche.me/e/20/gkpj)