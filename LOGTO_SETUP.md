# Logto Authentication Setup Guide

This guide explains how to set up Logto authentication for the Backtrader platform.

## Overview

The platform has been integrated with [Logto](https://logto.io) for authentication:
- **Backend (Python/FastAPI)**: Validates JWT tokens from Logto
- **Frontend (React)**: Manages authentication flow and token injection
- **Protected Routes**: All `/api/*` endpoints require authentication
- **Unauthenticated Access**: Redirects to home page for login

## Prerequisites

1. **Logto Account**: Sign up at [Logto Cloud](https://cloud.logto.io) or self-host Logto
2. **Node.js 18+** and **Python 3.12+**
3. **npm** or **yarn** for frontend dependencies
4. **pip** for backend dependencies

## Step 1: Create Logto Applications

### 1.1 Create Backend API Resource

1. Go to Logto Console → **API Resources**
2. Click **Create API Resource**
3. Configure:
   - **Name**: `Backtrader API`
   - **API Identifier**: `http://localhost:8000` (development) or your production URL
4. Save the **API Identifier** (you'll need it for configuration)

### 1.2 Create Backend Application (Traditional Web)

1. Go to Logto Console → **Applications**
2. Click **Create Application**
3. Select **Traditional Web**
4. Configure:
   - **Application Name**: `Backtrader Backend`
5. Save and note down:
   - **App ID**
   - **App Secret**

### 1.3 Create Frontend Application (Single Page App)

1. Go to Logto Console → **Applications**
2. Click **Create Application**
3. Select **Single Page Application**
4. Configure:
   - **Application Name**: `Backtrader Frontend`
   - **Redirect URIs**:
     - Development: `http://localhost:5173/callback`
     - Production: `https://yourdomain.com/callback`
   - **Post Logout Redirect URIs**:
     - Development: `http://localhost:5173`
     - Production: `https://yourdomain.com`
   - **CORS Allowed Origins**:
     - Development: `http://localhost:5173`
     - Production: `https://yourdomain.com`
5. Save and note down:
   - **App ID**

### 1.4 Link Frontend App to API Resource

1. In the Frontend Application settings
2. Go to **API Resources** tab
3. Click **Add API Resource**
4. Select the `Backtrader API` resource created earlier
5. Save

## Step 2: Configure Backend

### 2.1 Update Environment Variables

Edit `backend/.env`:

```env
# Logto Authentication Configuration
LOGTO_ENDPOINT=https://your-tenant.logto.app
LOGTO_APP_ID=your-backend-app-id
LOGTO_APP_SECRET=your-backend-app-secret
LOGTO_AUDIENCE=http://localhost:8000
```

**Replace:**
- `your-tenant.logto.app` → Your Logto tenant URL
- `your-backend-app-id` → App ID from Step 1.2
- `your-backend-app-secret` → App Secret from Step 1.2
- `http://localhost:8000` → API identifier from Step 1.1

### 2.2 Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

This installs:
- `logto>=0.2.1` - Logto Python SDK
- `python-jose[cryptography]>=3.3.0` - JWT verification
- `requests>=2.31.0` - HTTP client

### 2.3 Verify Backend Setup

Start the backend server:

```bash
cd backend
python main.py
```

You should see:
```
Logto authentication initialized: https://your-tenant.logto.app
```

If you see a warning about missing Logto configuration, double-check your `.env` file.

## Step 3: Configure Frontend

### 3.1 Update Environment Variables

Edit `frontend/.env`:

```env
# Logto Authentication Configuration (Development)
VITE_LOGTO_ENDPOINT=https://your-tenant.logto.app
VITE_LOGTO_APP_ID=your-frontend-app-id
VITE_LOGTO_REDIRECT_URI=http://localhost:5173/callback
VITE_LOGTO_POST_LOGOUT_REDIRECT_URI=http://localhost:5173
VITE_API_RESOURCE=http://localhost:8000
```

**Replace:**
- `your-tenant.logto.app` → Your Logto tenant URL
- `your-frontend-app-id` → App ID from Step 1.3
- `http://localhost:8000` → API identifier from Step 1.1

### 3.2 Create Production Environment File

Create `frontend/.env.production`:

```env
# Logto Authentication Configuration (Production)
VITE_LOGTO_ENDPOINT=https://your-tenant.logto.app
VITE_LOGTO_APP_ID=your-frontend-app-id
VITE_LOGTO_REDIRECT_URI=https://yourdomain.com/callback
VITE_LOGTO_POST_LOGOUT_REDIRECT_URI=https://yourdomain.com
VITE_API_RESOURCE=https://yourdomain.com
```

### 3.3 Install Dependencies

```bash
cd frontend
npm install
```

This installs:
- `@logto/react` - Logto React SDK

### 3.4 Start Frontend Development Server

```bash
cd frontend
npm run dev
```

Frontend should start at `http://localhost:5173`

## Step 4: Test Authentication

### 4.1 Test Login Flow

1. Open browser to `http://localhost:5173`
2. You should see the **Home/Login page**
3. Click **Sign In**
4. You'll be redirected to Logto login page
5. Sign in with your credentials (or create a new account)
6. After successful authentication, you'll be redirected to `/app`
7. You should see the main application with your user avatar in the header

### 4.2 Test API Protection

1. Open browser DevTools → Network tab
2. Navigate to `/app` (main strategy page)
3. Observe API requests to `/api/strategies`
4. Check request headers - should include: `Authorization: Bearer <token>`
5. Response should be `200 OK` with strategy list

### 4.3 Test Logout

1. Click your user avatar in the top-right header
2. Click **Logout**
3. You should be redirected to the home page (`/`)
4. Try accessing `/app` directly - you should be redirected to `/`

### 4.4 Test Unauthorized Access

1. Open a new incognito/private browser window
2. Navigate to `http://localhost:5173/app`
3. You should be immediately redirected to `/` (home page)
4. Try making API requests without token:
   ```bash
   curl http://localhost:8000/api/strategies
   ```
   Should return: `401 Unauthorized`

## Step 5: Production Deployment

### 5.1 Update Backend .env for Production

```env
LOGTO_ENDPOINT=https://your-tenant.logto.app
LOGTO_APP_ID=your-backend-app-id
LOGTO_APP_SECRET=your-backend-app-secret
LOGTO_AUDIENCE=https://yourdomain.com
```

### 5.2 Update CORS Settings

Edit `backend/api.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],  # Replace wildcard
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 5.3 Update Logto Console

1. Go to Frontend Application settings in Logto Console
2. Update **Redirect URIs**: Add `https://yourdomain.com/callback`
3. Update **Post Logout Redirect URIs**: Add `https://yourdomain.com`
4. Update **CORS Allowed Origins**: Add `https://yourdomain.com`

### 5.4 Build Frontend

```bash
cd frontend
npm run build
```

Build output goes to `frontend/dist/`

### 5.5 Deploy

Follow your standard deployment process. Ensure:
- Environment variables are set correctly
- HTTPS is enabled (required for secure token transmission)
- Backend serves frontend static files from `/backend/resources/frontend/`

## Troubleshooting

### Issue: "401 Unauthorized" on API requests

**Solution:**
1. Check browser DevTools → Network tab
2. Verify `Authorization: Bearer <token>` header is present
3. Check backend logs for token verification errors
4. Ensure `LOGTO_AUDIENCE` matches between frontend (`VITE_API_RESOURCE`) and backend

### Issue: "Failed to get access token"

**Solution:**
1. Verify frontend `.env` has correct `VITE_LOGTO_APP_ID`
2. Ensure Frontend Application in Logto Console has API Resource linked
3. Check browser console for detailed error messages

### Issue: Infinite redirect loop

**Solution:**
1. Verify `VITE_LOGTO_REDIRECT_URI` matches exactly what's configured in Logto Console
2. Check that `/callback` route exists and is public (not protected)
3. Clear browser cache and cookies

### Issue: Backend fails to start with Logto error

**Solution:**
1. Verify all `LOGTO_*` environment variables are set in `backend/.env`
2. Check `LOGTO_ENDPOINT` is accessible (not blocked by firewall)
3. Verify `LOGTO_APP_SECRET` is correct (no extra spaces or quotes)

### Issue: CORS errors in browser console

**Solution:**
1. Ensure Frontend Application in Logto Console has CORS origins configured
2. Update `backend/api.py` to allow your frontend origin
3. Verify Vite proxy is configured correctly in `frontend/vite.config.js`

## Architecture Details

### Authentication Flow

```
User → Home Page (/) → Click "Sign In"
  ↓
Logto Login Page (hosted by Logto)
  ↓
User enters credentials
  ↓
Logto redirects to: http://localhost:5173/callback?code=...
  ↓
Callback page exchanges code for tokens
  ↓
Frontend stores access token (in memory via Logto SDK)
  ↓
Redirect to /app (main application)
  ↓
All API requests include: Authorization: Bearer <token>
  ↓
Backend verifies token using Logto JWKS endpoint
  ↓
Valid token → 200 OK | Invalid → 401 Unauthorized
```

### Token Management

- **Access Token**: Short-lived (default: 1 hour), included in API requests
- **Refresh Token**: Long-lived, used to get new access tokens
- **Token Storage**: Managed by `@logto/react` SDK (memory + sessionStorage)
- **Token Refresh**: Automatic via Logto SDK when access token expires

### Protected Routes

**Backend:**
- All `/api/*` endpoints require valid JWT token
- Exception: Static file serving (`/images/*`, frontend SPA)

**Frontend:**
- `/` - Public (home/login page)
- `/callback` - Public (OAuth callback handler)
- `/app/*` - Protected (requires authentication)

### Security Considerations

1. **HTTPS Required**: Use HTTPS in production for secure token transmission
2. **CORS Configuration**: Restrict `allow_origins` to specific domains in production
3. **Token Expiration**: Tokens expire after 1 hour (configurable in Logto)
4. **JWT Signature Verification**: Backend verifies token signature using JWKS
5. **No Secrets in Frontend**: Frontend only has public App ID, not App Secret

## Additional Resources

- [Logto Documentation](https://docs.logto.io)
- [Logto React SDK](https://docs.logto.io/sdk/react/)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [JWT.io](https://jwt.io) - Decode and inspect JWT tokens

## Support

For issues specific to Logto integration:
1. Check this guide's Troubleshooting section
2. Review Logto Console settings
3. Check browser console and network tab for errors
4. Review backend logs for token verification errors

For Logto-specific questions:
- [Logto Discord Community](https://discord.gg/UEPaF3j5e6)
- [Logto GitHub Issues](https://github.com/logto-io/logto/issues)
