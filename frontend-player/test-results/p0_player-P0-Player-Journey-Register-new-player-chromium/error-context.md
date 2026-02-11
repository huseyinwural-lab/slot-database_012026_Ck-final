# Page snapshot

```yaml
- generic [ref=e3]:
  - generic [ref=e4]: "[plugin:vite:import-analysis] Failed to resolve import \"@/domain/auth/storage\" from \"src/telemetry/index.js\". Does the file exist?"
  - generic [ref=e5]: /app/frontend-player/src/telemetry/index.js:2:32
  - generic [ref=e6]: "1 | import { telemetryApi } from '@/infra/api/telemetry'; 2 | import { getStoredUser } from '@/domain/auth/storage'; | ^ 3 | 4 | const SESSION_KEY = 'player_session_id';"
  - generic [ref=e7]: at TransformPluginContext._formatError (file:///app/frontend-player/node_modules/vite/dist/node/chunks/dep-BK3b2jBa.js:49258:41) at TransformPluginContext.error (file:///app/frontend-player/node_modules/vite/dist/node/chunks/dep-BK3b2jBa.js:49253:16) at normalizeUrl (file:///app/frontend-player/node_modules/vite/dist/node/chunks/dep-BK3b2jBa.js:64307:23) at async file:///app/frontend-player/node_modules/vite/dist/node/chunks/dep-BK3b2jBa.js:64439:39 at async Promise.all (index 1) at async TransformPluginContext.transform (file:///app/frontend-player/node_modules/vite/dist/node/chunks/dep-BK3b2jBa.js:64366:7) at async PluginContainer.transform (file:///app/frontend-player/node_modules/vite/dist/node/chunks/dep-BK3b2jBa.js:49099:18) at async loadAndTransform (file:///app/frontend-player/node_modules/vite/dist/node/chunks/dep-BK3b2jBa.js:51978:27) at async viteTransformMiddleware (file:///app/frontend-player/node_modules/vite/dist/node/chunks/dep-BK3b2jBa.js:62106:24
  - generic [ref=e8]:
    - text: Click outside, press Esc key, or fix the code to dismiss.
    - text: You can also disable this overlay by setting
    - code [ref=e9]: server.hmr.overlay
    - text: to
    - code [ref=e10]: "false"
    - text: in
    - code [ref=e11]: vite.config.js
    - text: .
```