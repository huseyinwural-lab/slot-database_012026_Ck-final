# Access Control Matrix (BAU-S0)

| Role | Prod DB Read | Prod DB Write | S3 Archive Read | S3 Archive Delete | Deploy |
|------|--------------|---------------|-----------------|-------------------|--------|
| **Ops Lead** | ✅ | ⚠️ (Break-glass) | ✅ | ❌ | ✅ |
| **DevOps** | ✅ | ❌ | ✅ | ❌ | ✅ |
| **Developer**| ❌ | ❌ | ❌ | ❌ | ❌ |
| **Compliance**| ✅ (Replica) | ❌ | ✅ | ❌ | ❌ |
| **System** | ✅ | ✅ | ✅ | ✅ (Lifecycle) | - |

**Policy:**
1. No direct DB write access for humans. Use Admin Panel or Script.
2. S3 Deletion only via automated Lifecycle Policy.
3. MFA Mandatory for all Prod Access.
