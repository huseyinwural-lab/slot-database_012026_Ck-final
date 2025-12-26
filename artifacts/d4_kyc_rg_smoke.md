# KYC & RG Smoke Test

- ERROR: (sqlite3.IntegrityError) NOT NULL constraint failed: robotdefinition.schema_version
[SQL: 
                INSERT INTO robotdefinition (id, name, config, config_hash, is_active, created_at, updated_at)
                VALUES (?, ?, '{}', 'hash1', 1, ?, ?)
            ]
[parameters: ('75394ee3-b4e8-467e-8408-9e02284c3653', 'Smoke Robot 4d6d3a08', datetime.datetime(2025, 12, 26, 20, 37, 23, 554104, tzinfo=datetime.timezone.utc), datetime.datetime(2025, 12, 26, 20, 37, 23, 554104, tzinfo=datetime.timezone.utc))]
(Background on this error at: https://sqlalche.me/e/20/gkpj)