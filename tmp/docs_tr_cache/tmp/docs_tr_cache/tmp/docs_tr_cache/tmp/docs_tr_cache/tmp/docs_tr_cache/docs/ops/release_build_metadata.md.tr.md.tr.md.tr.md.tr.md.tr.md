# Build Metadata Visibility (P3-REL-002)

## Goal
Make it obvious what version/commit is running in staging/prod.

## Where metadata is exposed
### Backend
1) **Boot log**
- Structured log event: `event=service.boot`
- Includes fields: `service`, `version`, `git_sha`, `build_time`

2) **Version endpoint**
- `GET /api/version` (public)
- Returns only safe fields:
  - `service`, `version`, `git_sha`, `build_time`

### Frontend (Admin)
- Settings → **Versions** tab
- Displays:
  - UI Version (`REACT_APP_VERSION`)
  - UI Git SHA (`REACT_APP_GIT_SHA`)
  - UI Build Time (`REACT_APP_BUILD_TIME`)
- Button: “Check Backend Version” calls `/api/version`

## CI / Build args
Recommended build args/env:
- `APP_VERSION` (from repo `VERSION`)
- `GIT_SHA` (short sha)
- `BUILD_TIME` (UTC ISO-8601)

## Security
- Do not include env/hostname/config values.
- Do not include secrets.
