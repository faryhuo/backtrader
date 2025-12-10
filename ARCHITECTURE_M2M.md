# Architecture Overview: M2M Authentication

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Browser (Frontend)                       │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              React Application (Port 5173)                │  │
│  │                                                            │  │
│  │  - No authentication required                             │  │
│  │  - Direct API calls (no Bearer token)                     │  │
│  │  - Public access to all features                          │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              │                                   │
└──────────────────────────────┼───────────────────────────────────┘
                               │
                               │ HTTP Requests
                               │ (No Authentication)
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Backend Server (Port 8000)                    │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    FastAPI Application                    │  │
│  │                                                            │  │
│  │  Public API Endpoints:                                    │  │
│  │  - GET  /api/strategies                                   │  │
│  │  - GET  /api/strategy?name=...                            │  │
│  │  - POST /api/strategy                                     │  │
│  │  - POST /api/backtest                                     │  │
│  │  - POST /api/data                                         │  │
│  │  - POST /api/analyze                                      │  │
│  │  - POST /api/ai_analyze                                   │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              │                                   │
│                              │ When needed for                   │
│                              │ external API calls                │
│                              ▼                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              M2M Authentication Module                    │  │
│  │              (backend/auth.py)                            │  │
│  │                                                            │  │
│  │  1. Check token cache                                     │  │
│  │  2. If expired/missing → Request new token                │  │
│  │  3. Cache token (expires in ~1 hour)                      │  │
│  │  4. Return valid token                                    │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              │                                   │
└──────────────────────────────┼───────────────────────────────────┘
                               │
                               │ OAuth 2.0 Client Credentials
                               │ POST /oidc/token
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                       Logto Server                               │
│                  (https://logto.fary.chat)                       │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              M2M Application                              │  │
│  │                                                            │  │
│  │  App ID: hnsx3ou27mrx1cwx3ux3i                            │  │
│  │  App Secret: upImmofjndDuad3n1IuXXrorjFnAZ4wL             │  │
│  │                                                            │  │
│  │  Linked to API Resource:                                  │  │
│  │    https://logto.fary.chat/api                            │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              │                                   │
│                              │ Issues Access Token               │
│                              ▼                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │            Token Response (JWT)                           │  │
│  │                                                            │  │
│  │  {                                                         │  │
│  │    "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6...",     │  │
│  │    "expires_in": 3600,                                    │  │
│  │    "token_type": "Bearer"                                 │  │
│  │  }                                                         │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## Authentication Flow Comparison

### Traditional Web App Flow (Old)

```
┌──────────┐         ┌──────────┐         ┌──────────┐         ┌──────────┐
│  User    │         │ Frontend │         │ Backend  │         │  Logto   │
└────┬─────┘         └────┬─────┘         └────┬─────┘         └────┬─────┘
     │                    │                    │                    │
     │  1. Open /app      │                    │                    │
     ├───────────────────>│                    │                    │
     │                    │                    │                    │
     │  2. Redirect to    │                    │                    │
     │     /login         │                    │                    │
     │<───────────────────┤                    │                    │
     │                    │                    │                    │
     │  3. Click "Sign In"│                    │                    │
     ├───────────────────>│                    │                    │
     │                    │  4. Redirect to    │                    │
     │                    │     Logto OAuth    │                    │
     │                    ├───────────────────────────────────────>│
     │                    │                    │                    │
     │  5. Enter credentials                   │                    │
     ├────────────────────────────────────────────────────────────>│
     │                    │                    │                    │
     │  6. Redirect back with code             │                    │
     │<────────────────────────────────────────────────────────────┤
     │                    │                    │                    │
     │                    │  7. Exchange code for token             │
     │                    ├───────────────────────────────────────>│
     │                    │                    │                    │
     │                    │  8. Return access token                 │
     │                    │<───────────────────────────────────────┤
     │                    │                    │                    │
     │  9. Store token    │                    │                    │
     │    in memory       │                    │                    │
     │                    │                    │                    │
     │ 10. API request    │                    │                    │
     │    with Bearer token│                   │                    │
     ├───────────────────>│───────────────────>│                    │
     │                    │                    │                    │
     │                    │  11. Verify token  │                    │
     │                    │    (check JWKS)    │                    │
     │                    │                    │<──────────────────>│
     │                    │                    │                    │
     │                    │  12. Return data   │                    │
     │<───────────────────┤<───────────────────┤                    │
     │                    │                    │                    │
```

### M2M Flow (New)

```
┌──────────┐         ┌──────────┐         ┌──────────┐         ┌──────────┐
│  User    │         │ Frontend │         │ Backend  │         │  Logto   │
└────┬─────┘         └────┬─────┘         └────┬─────┘         └────┬─────┘
     │                    │                    │                    │
     │  1. Open /app      │                    │                    │
     ├───────────────────>│                    │                    │
     │                    │                    │                    │
     │  2. Show app       │                    │                    │
     │    immediately     │                    │                    │
     │<───────────────────┤                    │                    │
     │                    │                    │                    │
     │  3. API request    │                    │                    │
     │    (no token)      │                    │                    │
     ├───────────────────>│───────────────────>│                    │
     │                    │                    │                    │
     │                    │  4. Process        │                    │
     │                    │     request        │                    │
     │                    │                    │                    │
     │                    │  5. Return data    │                    │
     │<───────────────────┤<───────────────────┤                    │
     │                    │                    │                    │
     │                    │                    │                    │
     │           (If backend needs to call external API)            │
     │                    │                    │                    │
     │                    │                    │  6. Request M2M    │
     │                    │                    │     token (Client  │
     │                    │                    │     Credentials)   │
     │                    │                    ├───────────────────>│
     │                    │                    │                    │
     │                    │                    │  7. Validate creds │
     │                    │                    │     & issue token  │
     │                    │                    │<───────────────────┤
     │                    │                    │                    │
     │                    │                    │  8. Cache token    │
     │                    │                    │     (1 hour)       │
     │                    │                    │                    │
     │                    │                    │  9. Call external  │
     │                    │                    │     API with token │
     │                    │                    │───────────────────>│
     │                    │                    │      External API  │
     │                    │                    │                    │
```

## File Structure Changes

### Removed Files
```
frontend/src/
├── providers/
│   └── LogtoProvider.jsx          ❌ REMOVED
├── components/
│   └── Auth/
│       └── PrivateRoute.jsx       ❌ REMOVED
└── pages/
    ├── Home.jsx                   ❌ REMOVED (login page)
    └── Callback.jsx               ❌ REMOVED (OAuth callback)
```

### Modified Files
```
backend/
├── auth.py                        ✏️  REFACTORED (M2M)
├── api.py                         ✏️  UPDATED (startup message)
├── .env                           ✏️  NEW VARIABLES (M2M)
├── requirements.txt               ✏️  REMOVED logto SDK
└── routes/
    ├── api_routes.py              ✏️  REMOVED auth dependencies
    └── ai_routes.py               ✏️  REMOVED auth dependencies

frontend/src/
├── App.jsx                        ✏️  SIMPLIFIED (no auth)
├── services/
│   └── api.js                     ✏️  REMOVED token injection
└── components/
    └── Layout/
        └── Layout.jsx             ✏️  REMOVED user menu
```

### New Files
```
backend/
└── test_m2m_auth.py              ✅ NEW (M2M test script)

root/
├── LOGTO_M2M_SETUP.md            ✅ NEW (detailed setup)
├── M2M_MIGRATION_SUMMARY.md      ✅ NEW (change summary)
├── M2M_QUICK_START.md            ✅ NEW (quick reference)
└── ARCHITECTURE_M2M.md           ✅ NEW (this file)
```

## Token Lifecycle

```
┌─────────────────────────────────────────────────────────────┐
│                    M2M Token Lifecycle                       │
└─────────────────────────────────────────────────────────────┘

1. Backend Starts
   ├─> Load M2M config from .env
   └─> Initialize empty token cache

2. First API Call Requiring External Auth
   ├─> Call get_m2m_token()
   ├─> Check cache (empty)
   ├─> Request token from Logto
   │   ├─> POST /oidc/token
   │   ├─> grant_type=client_credentials
   │   ├─> resource=https://logto.fary.chat/api
   │   └─> auth=(app_id, app_secret)
   ├─> Receive token (expires in 3600s)
   ├─> Cache token with expiry (3600 - 300 = 3300s)
   └─> Return token

3. Subsequent Calls (within 55 minutes)
   ├─> Call get_m2m_token()
   ├─> Check cache (valid)
   └─> Return cached token (instant)

4. After 55 Minutes
   ├─> Call get_m2m_token()
   ├─> Check cache (expired)
   ├─> Request new token from Logto
   ├─> Cache new token
   └─> Return new token

5. Server Restart
   ├─> Token cache cleared
   └─> Back to step 2
```

## Security Model

### Old Model: User-Based Authentication
```
┌──────────────────────────────────────────────┐
│           Security Boundaries                 │
├──────────────────────────────────────────────┤
│ User → Login → Token → API Access            │
│                                               │
│ ✓ Per-user permissions                       │
│ ✓ User tracking                              │
│ ✓ Audit trails                               │
│ ✓ Role-based access control                  │
│                                               │
│ Use case: Multi-user SaaS application        │
└──────────────────────────────────────────────┘
```

### New Model: M2M Authentication
```
┌──────────────────────────────────────────────┐
│           Security Boundaries                 │
├──────────────────────────────────────────────┤
│ Backend → M2M Token → External API            │
│                                               │
│ ✓ Service-to-service auth                    │
│ ✓ Automated processes                        │
│ ✓ No user interaction                        │
│ ✗ No per-user permissions                    │
│                                               │
│ Use case: Internal tools, single-tenant apps │
└──────────────────────────────────────────────┘

⚠️  Consider adding:
    - API Keys for frontend → backend
    - Rate limiting
    - IP whitelisting
    - Request logging
```

## Environment Variables

### Backend (backend/.env)
```env
# M2M Authentication
LOGTO_ENDPOINT=https://logto.fary.chat
LOGTO_M2M_APP_ID=hnsx3ou27mrx1cwx3ux3i
LOGTO_M2M_APP_SECRET=upImmofjndDuad3n1IuXXrorjFnAZ4wL
LOGTO_API_RESOURCE=https://logto.fary.chat/api

# Other Services
OPENAI_API_KEY=sk-...
OPENAI_BASE_URL=https://api.gptgod.online/v1/
```

### Frontend (frontend/.env)
```env
# Optional: Only if backend is on different host
VITE_API_HOST=http://localhost:8000
```

## Deployment Considerations

### Development
```
Frontend (Vite):  localhost:5173
Backend (Daphne): localhost:8000
Logto:            logto.fary.chat

CORS: Allow all origins (*)
Auth: M2M for backend, public frontend
```

### Production
```
Frontend: https://yourdomain.com
Backend:  https://yourdomain.com/api
Logto:    logto.fary.chat

CORS: Restrict to frontend domain only
Auth: M2M for backend, consider API keys
HTTPS: Required for all communications
```

---

**Last Updated**: 2025-12-10
**Architecture Version**: 2.0 (M2M)
