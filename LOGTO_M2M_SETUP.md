# Logto M2M (Machine-to-Machine) Authentication Setup Guide

This guide explains the updated Logto integration using **Machine-to-Machine (M2M)** authentication instead of traditional web application flow.

## Overview

The platform has been refactored to use Logto M2M authentication:
- **Backend (Python/FastAPI)**: Obtains M2M access tokens using client credentials flow
- **Frontend (React)**: No authentication - direct API access
- **API Routes**: All `/api/*` endpoints are public (no user authentication required)
- **Use Case**: Backend can use M2M tokens to authenticate with external protected APIs

## What is M2M Authentication?

Machine-to-Machine (M2M) authentication is designed for:
- **Server-to-server communication**: Backend services calling other backend APIs
- **No user interaction**: The application itself authenticates, not individual users
- **Client Credentials Flow**: Uses OAuth 2.0 client credentials grant type
- **Service accounts**: The app acts as a "machine user" with its own identity

## Prerequisites

1. **Logto Account**: Sign up at [Logto Cloud](https://cloud.logto.io) or self-host Logto
2. **Python 3.12+**
3. **pip** for backend dependencies

## Step 1: Create Logto M2M Application

### 1.1 Create API Resource (if not exists)

1. Go to Logto Console → **API Resources**
2. Click **Create API Resource**
3. Configure:
   - **Name**: `Backtrader API`
   - **API Identifier**: `https://logto.fary.chat/api` (your API endpoint)
4. Save the **API Identifier**

### 1.2 Create M2M Application

1. Go to Logto Console → **Applications**
2. Click **Create Application**
3. Select **Machine-to-Machine**
4. Configure:
   - **Application Name**: `Backtrader M2M`
   - **Description**: Machine-to-machine authentication for backend services
5. Save and note down:
   - **App ID**: e.g., `hnsx3ou27mrx1cwx3ux3i`
   - **App Secret**: e.g., `upImmofjndDuad3n1IuXXrorjFnAZ4wL`

### 1.3 Link M2M App to API Resource

1. In the M2M Application settings
2. Go to **API Resources** tab
3. Click **Add API Resource**
4. Select the `Backtrader API` resource created earlier
5. Save

## Step 2: Configure Backend

### 2.1 Update Environment Variables

Edit `backend/.env`:

```env
# Logto M2M (Machine-to-Machine) Authentication Configuration
LOGTO_ENDPOINT=https://logto.fary.chat
LOGTO_M2M_APP_ID=hnsx3ou27mrx1cwx3ux3i
LOGTO_M2M_APP_SECRET=upImmofjndDuad3n1IuXXrorjFnAZ4wL
LOGTO_API_RESOURCE=https://logto.fary.chat/api
```

**Replace:**
- `https://logto.fary.chat` → Your Logto tenant URL
- `hnsx3ou27mrx1cwx3ux3i` → Your M2M App ID
- `upImmofjndDuad3n1IuXXrorjFnAZ4wL` → Your M2M App Secret
- `https://logto.fary.chat/api` → Your API resource identifier

### 2.2 Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

This installs:
- `python-jose[cryptography]>=3.3.0` - JWT handling
- `requests>=2.31.0` - HTTP client for token requests

### 2.3 Verify Backend Setup

Start the backend server:

```bash
cd backend
python main.py
```

You should see:
```
Logto M2M authentication initialized: https://logto.fary.chat
API Resource: https://logto.fary.chat/api
M2M authentication is ready for backend-to-backend API calls
```

## Step 3: Frontend Configuration (Simplified)

### 3.1 No Authentication Required

The frontend no longer requires Logto configuration. All frontend `.env` files can remove Logto variables:

**Remove these from `frontend/.env` (if present):**
```env
# These are no longer needed
VITE_LOGTO_ENDPOINT=...
VITE_LOGTO_APP_ID=...
VITE_LOGTO_REDIRECT_URI=...
VITE_LOGTO_POST_LOGOUT_REDIRECT_URI=...
VITE_API_RESOURCE=...
```

### 3.2 Install Frontend Dependencies

```bash
cd frontend
npm install
```

### 3.3 Start Frontend Development Server

```bash
cd frontend
npm run dev
```

Frontend starts at `http://localhost:5173` and directly accesses the backend APIs without authentication.

## Step 4: Test the Application

### 4.1 Test Backend Startup

```bash
cd backend
python main.py
```

Verify you see the M2M initialization message without errors.

### 4.2 Test Frontend Access

1. Open browser to `http://localhost:5173`
2. You should be redirected to `/app` automatically
3. No login page - direct access to the application
4. Test API calls:
   - Navigate to strategy page
   - Run a backtest
   - All operations should work without authentication prompts

### 4.3 Test API Endpoints

All API endpoints are now public:

```bash
# Test strategies list
curl http://localhost:8000/api/strategies

# Test data fetch
curl -X POST http://localhost:8000/api/data \
  -H "Content-Type: application/json" \
  -d '{"ticker":"AAPL","start_date":"2024-01-01","end_date":"2024-12-31"}'
```

Should return `200 OK` without requiring authentication.

## How M2M Authentication Works

### Backend M2M Flow

```
Backend Service → Request Token from Logto
  ↓
POST https://logto.fary.chat/oidc/token
  grant_type=client_credentials
  resource=https://logto.fary.chat/api
  Authorization: Basic <app_id:app_secret>
  ↓
Logto validates credentials
  ↓
Returns Access Token (JWT)
  ↓
Backend caches token (expires in 1 hour)
  ↓
Backend uses token to call protected external APIs:
  Authorization: Bearer <token>
```

### Frontend → Backend Flow

```
Frontend (React) → Direct API Call
  ↓
GET/POST http://localhost:8000/api/*
  (No Authorization header)
  ↓
Backend processes request
  (No authentication check)
  ↓
Returns response
```

## Using M2M Tokens in Your Code

### Example: Call External Protected API

If you need to call an external API that requires M2M authentication:

```python
from fastapi import APIRouter, Depends
from auth import get_m2m_token
import requests

router = APIRouter()

@router.get("/external-data")
async def fetch_external_data(token: str = Depends(get_m2m_token)):
    """
    Example endpoint that calls an external protected API
    using the M2M access token
    """
    headers = {
        "Authorization": f"Bearer {token}"
    }

    response = requests.get(
        "https://external-api.example.com/data",
        headers=headers
    )

    return response.json()
```

### Token Caching

The M2M token is automatically cached for performance:
- **Cache Duration**: Until 5 minutes before expiration
- **Auto-Refresh**: New token requested when cache expires
- **Thread-Safe**: Single token shared across all requests

To manually clear the cache:

```python
from auth import clear_token_cache

clear_token_cache()
```

## Architecture Comparison

### Before (Traditional Web App)

```
User → Frontend Login → Logto OAuth Flow
  ↓
User gets access token
  ↓
Frontend stores token in browser
  ↓
Frontend includes token in API requests
  ↓
Backend verifies user token
  ↓
Protected API endpoints
```

### After (M2M)

```
User → Frontend (no login)
  ↓
Direct API access
  ↓
Backend obtains its own M2M token (if needed)
  ↓
Backend uses M2M token for external API calls
  ↓
Public API endpoints (or protected by other means)
```

## Security Considerations

### Important Notes

1. **No User Authentication**: The current setup removes user-level authentication
   - All API endpoints are publicly accessible
   - Consider implementing API keys, rate limiting, or IP whitelisting if needed

2. **M2M Token Security**:
   - **Never expose** `LOGTO_M2M_APP_SECRET` in frontend code
   - Keep credentials in backend `.env` file only
   - Use environment variables in production

3. **Production Deployment**:
   - Use HTTPS for all communications
   - Restrict CORS origins in `backend/api.py`
   - Consider adding middleware for API protection (rate limiting, IP filtering, etc.)

4. **Token Storage**:
   - M2M tokens are cached in-memory on the backend
   - Tokens are never sent to frontend
   - Token cache is cleared on server restart

## When to Use M2M Authentication

**Use M2M when:**
- ✅ Backend needs to call other protected APIs as itself
- ✅ No user-specific permissions required
- ✅ Server-to-server communication
- ✅ Service accounts and automated processes

**Don't use M2M when:**
- ❌ Need user-specific authentication
- ❌ Need to track individual user actions
- ❌ Require user consent for operations
- ❌ Need role-based access control (RBAC)

## Troubleshooting

### Issue: "Failed to obtain M2M token"

**Solution:**
1. Verify `LOGTO_M2M_APP_ID` and `LOGTO_M2M_APP_SECRET` are correct
2. Check that M2M app has API resource linked in Logto Console
3. Ensure `LOGTO_API_RESOURCE` matches the API identifier in Logto Console
4. Check network connectivity to Logto endpoint

### Issue: Backend fails to start

**Solution:**
1. Verify all `LOGTO_M2M_*` environment variables are set in `backend/.env`
2. Check `LOGTO_ENDPOINT` is accessible (not blocked by firewall)
3. Ensure no extra spaces or quotes in credentials

### Issue: Frontend build errors

**Solution:**
1. Remove old Logto imports from any remaining components
2. Run `npm install` to ensure dependencies are up to date
3. Check for any references to `@logto/react` and remove them

## Migration from Traditional Web App

If you're migrating from the old setup:

1. **Remove frontend Logto dependencies**:
   ```bash
   cd frontend
   npm uninstall @logto/react
   ```

2. **Update environment variables**:
   - Remove `VITE_LOGTO_*` from frontend `.env`
   - Add `LOGTO_M2M_*` to backend `.env`

3. **Remove authentication components**:
   - Delete `src/providers/LogtoProvider.jsx`
   - Delete `src/components/Auth/PrivateRoute.jsx`
   - Delete `src/pages/Home.jsx` (login page)
   - Delete `src/pages/Callback.jsx`

4. **Rebuild frontend**:
   ```bash
   cd frontend
   npm run build
   ```

## Additional Resources

- [Logto M2M Documentation](https://docs.logto.io/docs/recipes/integrate-logto/machine-to-machine/)
- [OAuth 2.0 Client Credentials](https://oauth.net/2/grant-types/client-credentials/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)

## Support

For issues specific to Logto M2M integration:
1. Check this guide's Troubleshooting section
2. Review Logto Console M2M application settings
3. Check backend logs for token request errors

For Logto-specific questions:
- [Logto Discord Community](https://discord.gg/UEPaF3j5e6)
- [Logto GitHub Issues](https://github.com/logto-io/logto/issues)
