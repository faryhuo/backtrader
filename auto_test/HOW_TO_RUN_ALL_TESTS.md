# How to Run All 44 Tests (Instead of Skipping 38)

Currently: **6 passed, 38 skipped**  
Goal: **Run all 44 tests**

## Prerequisites

### 1. Get Authentication Token

The 34 e2e API tests need a valid JWT token. Here's how to get one:

**Method A: From Browser (Easiest)**

1. Open your frontend: http://localhost:5173
2. Login with your Logto account
3. Open browser dev tools (F12)
4. Go to Console tab
5. Run this to get your token:
   ```javascript
   localStorage.getItem('logto:idToken')
   ```
6. Copy the token (the long string)

**Method B: From Backend Logs**

1. Login to your frontend
2. Check backend logs for the JWT token in requests
3. Copy the `Authorization: Bearer <token>` value

**Method C: Use Logto API**

```bash
# Get token from Logto directly (if you have credentials)
curl -X POST https://your-logto-domain/oidc/token \
  -d "grant_type=password" \
  -d "client_id=your_client_id" \
  -d "username=test@example.com" \
  -d "password=yourpassword"
```

### 2. Start Frontend Server

```bash
cd d:\Project\backtrader\frontend
npm run dev
# Wait for "Local: http://localhost:5173"
```

## Run All Tests

### Windows (PowerShell)

```powershell
# Set the auth token
$env:TEST_AUTH_TOKEN = "eyJhbGciOiJSUzI1Ni..." # Your actual token

# Run all tests
cd d:\Project\backtrader\auto_test
pytest e2e/ smoke/ -v

# Or use the batch file
.\run_tests.bat all
```

### Expected Results

With authentication AND frontend running:
```
Strategy tests: 14 tests PASS ✅
Backtest tests: 13 tests PASS ✅
Live trading tests: 9 tests PASS ✅
Smoke tests: 10 tests PASS ✅
Total: 46 passed, 0 skipped
```

## Quick Commands

```bash
# 1. Get token and set it
set TEST_AUTH_TOKEN=<your_token_here>

# 2. Start frontend in another terminal
cd frontend && npm run dev

# 3. Run all tests
cd auto_test
.\run_tests.bat all
```

## Token Expiration

JWT tokens expire! If tests start failing with 401/403:
1. Get a fresh token from browser
2. Update TEST_AUTH_TOKEN
3. Run tests again

## Alternative: Mock Auth in Backend

If you want tests to work without real tokens, modify backend to accept test tokens:

```python
# In backend auth middleware
if os.getenv("TESTING") == "true":
    # Accept any token starting with "test_"
    if token.startswith("test_"):
        return {"sub": "test_user", "username": "testuser"}
```

Then run tests with:
```bash
set TESTING=true
pytest e2e/ -v
```
