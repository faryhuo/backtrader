# M2M Authentication Quick Start Guide

## 🚀 Quick Setup (5 Minutes)

### 1. Backend Configuration

Edit `backend/.env`:
```env
LOGTO_ENDPOINT=https://logto.fary.chat
LOGTO_M2M_APP_ID=hnsx3ou27mrx1cwx3ux3i
LOGTO_M2M_APP_SECRET=upImmofjndDuad3n1IuXXrorjFnAZ4wL
LOGTO_API_RESOURCE=https://logto.fary.chat/api
```

### 2. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 3. Test M2M Authentication

```bash
cd backend
python test_m2m_auth.py
```

Expected output:
```
✓ Configuration loaded successfully
✓ Token acquired successfully
✓ Token caching works correctly
✓ All Critical Tests Passed!
```

### 4. Start Backend

```bash
cd backend
python main.py
```

Look for:
```
Logto M2M authentication initialized: https://logto.fary.chat
API Resource: https://logto.fary.chat/api
M2M authentication is ready for backend-to-backend API calls
```

### 5. Start Frontend

```bash
cd frontend
npm install
npm run dev
```

### 6. Test Application

Open browser to `http://localhost:5173`

You should:
- ✅ See the application immediately (no login page)
- ✅ Be able to run backtests
- ✅ View strategies
- ✅ Access all features without authentication

## 🔑 Key Differences from Old Setup

| Aspect | Before (Traditional) | After (M2M) |
|--------|---------------------|-------------|
| User Login | Required | Not required |
| Frontend Auth | Yes (@logto/react) | No |
| Backend Auth | Validates user tokens | Obtains M2M tokens |
| API Protection | Required Bearer token | Public |
| Use Case | Multi-user app | Single-tenant/Internal |

## 📝 Common Tasks

### Obtain M2M Token in Your Code

```python
from fastapi import Depends
from auth import get_m2m_token

@router.get("/external-api")
async def call_external(token: str = Depends(get_m2m_token)):
    headers = {"Authorization": f"Bearer {token}"}
    # Use token to call external protected API
    ...
```

### Clear Token Cache

```python
from auth import clear_token_cache

clear_token_cache()  # Force new token acquisition
```

### Check Token Expiration

Tokens are automatically refreshed 5 minutes before expiration. No manual handling needed.

## 🐛 Troubleshooting

### Problem: "Missing required Logto M2M configuration"

**Solution**: Check `backend/.env` has all required variables:
- `LOGTO_ENDPOINT`
- `LOGTO_M2M_APP_ID`
- `LOGTO_M2M_APP_SECRET`

### Problem: "Failed to obtain M2M token"

**Solution**:
1. Verify credentials are correct in Logto Console
2. Ensure M2M app is linked to API resource
3. Check `LOGTO_API_RESOURCE` matches API identifier

### Problem: Frontend shows old login page

**Solution**:
1. Clear browser cache
2. Rebuild frontend: `cd frontend && npm run build`
3. Restart dev server: `npm run dev`

## 📚 More Information

- **Detailed Setup**: See `LOGTO_M2M_SETUP.md`
- **Migration Details**: See `M2M_MIGRATION_SUMMARY.md`
- **Logto M2M Docs**: https://docs.logto.io/docs/recipes/integrate-logto/machine-to-machine/

## ✅ Verification Checklist

- [ ] Backend `.env` configured with M2M credentials
- [ ] `test_m2m_auth.py` passes all tests
- [ ] Backend starts without errors
- [ ] Frontend accessible without login
- [ ] Can run backtests successfully
- [ ] No authentication errors in browser console
- [ ] No authentication errors in backend logs

## 🎯 Next Steps

1. **Security**: Consider adding API keys or rate limiting for public endpoints
2. **Deployment**: Update CORS settings in production
3. **Monitoring**: Add logging for M2M token acquisition
4. **Cleanup**: Remove old authentication files and dependencies

---

**Need Help?**
- Check Troubleshooting section above
- Review detailed setup guide in `LOGTO_M2M_SETUP.md`
- Visit [Logto Discord](https://discord.gg/UEPaF3j5e6)
