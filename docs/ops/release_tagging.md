# Release Tagging Standard (P3-REL-001)

## Goal
- Standardize Docker image tags for deterministic deployments.
- **Do not use `latest`** in staging/prod.

## Tag format
Use:

```
vX.Y.Z-<gitsha>
```

Examples:
- `v1.4.0-8f2c1ab`
- `v0.3.2-a1b2c3d`

Notes:
- `gitsha` should be the **short** commit SHA (7–12 chars).
- Version is stored in repo root `VERSION`.

## Compose deployment (example)
Instead of building or using `latest`, pin images:

```yaml
services:
  backend:
    image: registry.example.com/casino/backend:v1.4.0-8f2c1ab
  frontend-admin:
    image: registry.example.com/casino/frontend-admin:v1.4.0-8f2c1ab
  frontend-player:
    image: registry.example.com/casino/frontend-player:v1.4.0-8f2c1ab
```

## Kubernetes deployment (short example)
Pin the image tag in your Deployment:

```yaml
spec:
  template:
    spec:
      containers:
        - name: backend
          image: registry.example.com/casino/backend:v1.4.0-8f2c1ab
```

## How to verify running version
- Backend: `GET /api/version`
- Backend logs: `event=service.boot` includes `version`, `git_sha`, `build_time`
- Admin UI: Settings → About/Version card displays `version` and `git_sha`

## Policy
- ✅ Allowed: pinned release tags `vX.Y.Z-<gitsha>`
- ❌ Forbidden in staging/prod: `latest`, unpinned tags
