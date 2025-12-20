# Backend Authentication Detection

The test suite now **automatically detects** if backend authentication is enabled or disabled!

## How It Works

1. **First test run**: Makes a test request to `/api/strategies` without token
2. **Status 200**: Auth is disabled → All tests run! ✅
3. **Status 503/401/403**: Auth is enabled → Tests skip unless `TEST_AUTH_TOKEN` provided

## Behavior

### Backend Auth Disabled (`AUTH_ENABLED=false`)

```bash
# Tests automatically detect and run everything
pytest e2e/ -v

Result: 40 tests PASS ✅ (no token needed!)
```

### Backend Auth Enabled (`AUTH_ENABLED=true`)

```bash
# Without token: Tests skip gracefully
pytest e2e/ -v
Result: 38 tests SKIPPED (need token)

# With token: Tests run
set TEST_AUTH_TOKEN=your_token
pytest e2e/ -v  
Result: 40 tests PASS ✅
```

## Manual Override

```bash
# Force skip auth tests even if backend allows it
set SKIP_AUTH_TESTS=true
pytest e2e/

# Force run auth tests (will fail if backend requires it)
set SKIP_AUTH_TESTS=false  
pytest e2e/
```

## Summary

✅ **Zero configuration needed** - tests adapt to backend settings  
✅ **Auth disabled** → All tests run automatically  
✅ **Auth enabled** → Tests skip gracefully (or run with token)
