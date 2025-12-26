# KYC & RG Smoke Test

- ERROR: (sqlite3.OperationalError) table ledgertransaction has no column named balance_after
[SQL: 
                INSERT INTO ledgertransaction (
                    id, tenant_id, player_id, type, amount, currency, status, created_at, balance_after
                )
                VALUES (
                    ?, ?, ?, 'deposit', 100.0, 'USD', 'deposit_succeeded', ?, 100.0
                )
            ]
[parameters: ('f90c3d22-6d42-40b2-b653-3e7aeeaba7c6', 'default_casino', 'f8dabe37-9c0c-422f-bde6-2d1952ee75af', datetime.datetime(2025, 12, 26, 20, 35, 33, 457394, tzinfo=datetime.timezone.utc))]
(Background on this error at: https://sqlalche.me/e/20/e3q8)