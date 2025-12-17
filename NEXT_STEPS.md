# Next Steps - Database-Backed Credentials Feature

## What's Been Completed ✅

The **backend** infrastructure for database-backed credential management is fully implemented:

- ✅ Encryption utilities (Fernet-based)
- ✅ Database schema extension (9 new credential fields)
- ✅ Migration script for existing databases
- ✅ Storage layer with CRUD operations
- ✅ ConfigManager for unified credential access
- ✅ CCXT integration (loads from database first)
- ✅ Credential validation utilities
- ✅ 5 new API endpoints for credential management
- ✅ Updated .env.template with encryption key instructions

**Total: ~1,843 lines of production code**

## What Remains ⏳

### 1. Frontend UI (Priority: HIGH)

**Files to modify:**

#### a. [frontend/src/services/api.js](frontend/src/services/api.js)
Add these methods to the API client:

```javascript
// Get all credentials (masked)
async getCredentials() {
    const res = await buildRequest('/settings/credentials');
    return await parseResponse(res);
}

// Update general credentials (OpenAI, Logto, Proxies)
async updateCredentials(credentials) {
    const res = await buildRequest('/settings/credentials', {
        method: 'PUT',
        body: JSON.stringify(credentials)
    });
    return await parseResponse(res);
}

// Update CCXT exchange credentials
async updateCCXTCredentials(exchange, mode, credentials) {
    const res = await buildRequest('/settings/credentials/ccxt', {
        method: 'PUT',
        body: JSON.stringify({ exchange, mode, ...credentials })
    });
    return await parseResponse(res);
}

// Reset credential to .env value
async resetCredential(credentialKey) {
    const res = await buildRequest(`/settings/credentials/${credentialKey}`, {
        method: 'DELETE'
    });
    return await parseResponse(res);
}

// Test credential validity
async testCredential(credentialType, params) {
    const res = await buildRequest('/settings/credentials/test', {
        method: 'POST',
        body: JSON.stringify({ credential_type: credentialType, ...params })
    });
    return await parseResponse(res);
}
```

#### b. [frontend/src/pages/Settings.jsx](frontend/src/pages/Settings.jsx)
Extend the existing Settings page with credential sections. Add these cards after the existing AI Settings card:

```jsx
// State management
const [credentials, setCredentials] = useState({
    openai: { api_key: '', base_url: '', api_key_source: 'env' },
    logto: { issuer: '', jwks_uri: '', audience: '', scopes: '', enable_login: true },
    proxies: { http_proxy: '', https_proxy: '' },
    exchanges: {
        binance: { paper: {}, live: {} },
        okx: { paper: {}, live: {} },
        bybit: { paper: {}, live: {} }
    }
});
const [testResults, setTestResults] = useState({});

// Load credentials on mount
useEffect(() => {
    loadCredentials();
}, []);

const loadCredentials = async () => {
    const result = await api.getCredentials();
    if (result.status === 'ok') {
        setCredentials(result.credentials);
    }
};

const handleTestCredential = async (type, params) => {
    setTestResults({ ...testResults, [type]: { loading: true } });
    const result = await api.testCredential(type, params);
    setTestResults({ ...testResults, [type]: {
        loading: false,
        valid: result.valid,
        message: result.message
    }});
};

// Add these Card components to JSX:

{/* OpenAI Configuration */}
<Card title="OpenAI Configuration" style={{ marginTop: 16 }}>
    <Form.Item label="API Key">
        <Input.Password
            value={credentials.openai.api_key}
            onChange={e => setCredentials({
                ...credentials,
                openai: { ...credentials.openai, api_key: e.target.value }
            })}
            placeholder={credentials.openai.api_key_source === 'env' ? 'Using .env value' : 'Enter API key'}
            addonAfter={
                <Tag color={credentials.openai.api_key_source === 'database' ? 'green' : 'blue'}>
                    {credentials.openai.api_key_source}
                </Tag>
            }
        />
        <Space style={{ marginTop: 8 }}>
            <Button
                size="small"
                onClick={() => handleTestCredential('openai', {
                    api_key: credentials.openai.api_key,
                    base_url: credentials.openai.base_url
                })}
                loading={testResults.openai?.loading}
            >
                Test Connection
            </Button>
            <Button
                size="small"
                danger
                onClick={async () => {
                    await api.resetCredential('openai_api_key');
                    loadCredentials();
                }}
            >
                Reset to .env
            </Button>
            {testResults.openai && !testResults.openai.loading && (
                <Tag color={testResults.openai.valid ? 'success' : 'error'}>
                    {testResults.openai.message}
                </Tag>
            )}
        </Space>
    </Form.Item>

    <Form.Item label="Base URL">
        <Input
            value={credentials.openai.base_url}
            onChange={e => setCredentials({
                ...credentials,
                openai: { ...credentials.openai, base_url: e.target.value }
            })}
            placeholder="https://api.openai.com/v1"
        />
    </Form.Item>

    <Form.Item>
        <Button
            type="primary"
            onClick={async () => {
                await api.updateCredentials({
                    openai_api_key: credentials.openai.api_key,
                    openai_base_url: credentials.openai.base_url
                });
                message.success('OpenAI credentials saved');
                loadCredentials();
            }}
        >
            Save OpenAI Credentials
        </Button>
    </Form.Item>
</Card>

{/* Exchange Credentials */}
<Card title="Exchange Credentials" style={{ marginTop: 16 }}>
    <Tabs items={[
        {
            key: 'binance',
            label: 'Binance',
            children: <ExchangeCredentialTabs exchange="binance" credentials={credentials} setCredentials={setCredentials} />
        },
        {
            key: 'okx',
            label: 'OKX',
            children: <ExchangeCredentialTabs exchange="okx" credentials={credentials} setCredentials={setCredentials} includePassphrase />
        },
        {
            key: 'bybit',
            label: 'Bybit',
            children: <ExchangeCredentialTabs exchange="bybit" credentials={credentials} setCredentials={setCredentials} />
        }
    ]} />
</Card>
```

#### c. Create helper component (optional but recommended)
**File**: [frontend/src/components/Settings/ExchangeCredentialTabs.jsx](frontend/src/components/Settings/ExchangeCredentialTabs.jsx)

```jsx
const ExchangeCredentialTabs = ({ exchange, credentials, setCredentials, includePassphrase }) => {
    return (
        <Tabs items={[
            {
                key: 'paper',
                label: 'Paper Trading (Testnet)',
                children: <ExchangeCredentialForm
                    exchange={exchange}
                    mode="paper"
                    credentials={credentials}
                    setCredentials={setCredentials}
                    includePassphrase={includePassphrase}
                />
            },
            {
                key: 'live',
                label: 'Live Trading',
                children: <ExchangeCredentialForm
                    exchange={exchange}
                    mode="live"
                    credentials={credentials}
                    setCredentials={setCredentials}
                    includePassphrase={includePassphrase}
                />
            }
        ]} />
    );
};
```

### 2. Service Integration (Priority: MEDIUM)

#### a. [backend/src/routes/ai_routes.py](backend/src/routes/ai_routes.py)
Replace OpenAI client initialization:

```python
# OLD:
from openai import AsyncOpenAI
client = AsyncOpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL")
)

# NEW:
from src.config.config_manager import ConfigManager
config_manager = ConfigManager(user.get("sub") if user else None)
openai_config = config_manager.get_openai_config()
client = AsyncOpenAI(**openai_config)
```

#### b. [backend/src/utils/auth.py](backend/src/utils/auth.py)
Add config manager for Logto settings:

```python
from src.config.config_manager import get_global_config_manager

def fetch_jwks() -> Dict[str, Any]:
    """Fetch JWKS from Logto (with database fallback)."""
    config = get_global_config_manager().get_logto_config()
    jwks_uri = config["jwks_uri"]
    # ... rest of logic
```

#### c. [backend/src/service/live_engine.py](backend/src/service/live_engine.py)
Pass user_id to CCXTStore:

```python
# In run_live() function:
def run_live(exchange_id, mode, strategy_name, user_id=None):  # Add user_id parameter
    store = CCXTStore(
        exchange_id=exchange_id,
        mode=mode,
        user_id=user_id  # Pass it to store
    )
```

#### d. [backend/src/routes/live_routes.py](backend/src/routes/live_routes.py)
Extract user_id and pass to live_engine:

```python
@router.post("/live/start")
def start_live_trading(request: LiveTradingRequest, user: dict = Depends(get_current_user)):
    user_id = user.get("sub") if user else None
    live_engine.run_live(
        exchange_id=request.exchange,
        mode=request.mode,
        strategy_name=request.strategy_name,
        user_id=user_id  # Pass user_id
    )
```

### 3. Documentation (Priority: LOW)

Update these files with comprehensive documentation:

- [ ] `backend/README.md` - Add encryption setup section
- [ ] `CLAUDE.md` - Document ConfigManager architecture
- [ ] Create `docs/CREDENTIAL_MANAGEMENT.md` - User guide

## Quick Start (For Immediate Testing)

### 1. Setup Encryption Key

```bash
cd backend
python -m src.utils.encryption
# Copy output to .env as ENCRYPTION_KEY=...
```

### 2. Run Migration

```bash
python -m src.db.migrations.add_credential_fields
```

### 3. Test API Endpoints (Using curl)

```bash
# Get credentials (will show .env values initially)
curl -X GET http://localhost:8000/api/settings/credentials \
  -H "Authorization: Bearer <your-token>"

# Update OpenAI credentials
curl -X PUT http://localhost:8000/api/settings/credentials \
  -H "Authorization: Bearer <your-token>" \
  -H "Content-Type: application/json" \
  -d '{"openai_api_key": "sk-test123", "openai_base_url": "https://api.openai.com/v1"}'

# Test OpenAI credentials
curl -X POST http://localhost:8000/api/settings/credentials/test \
  -H "Authorization: Bearer <your-token>" \
  -H "Content-Type: application/json" \
  -d '{"credential_type": "openai", "api_key": "sk-test123", "base_url": "https://api.openai.com/v1"}'

# Update Binance paper credentials
curl -X PUT http://localhost:8000/api/settings/credentials/ccxt \
  -H "Authorization: Bearer <your-token>" \
  -H "Content-Type: application/json" \
  -d '{"exchange": "binance", "mode": "paper", "api_key": "...", "secret": "..."}'

# Reset credential to .env value
curl -X DELETE http://localhost:8000/api/settings/credentials/openai_api_key \
  -H "Authorization: Bearer <your-token>"
```

## Testing Checklist

Before considering the feature complete:

- [ ] Encryption key generation works
- [ ] Database migration runs without errors
- [ ] API endpoints respond correctly (test with curl/Postman)
- [ ] Credentials are encrypted in database (check with DB browser)
- [ ] Fallback to .env works when database value is NULL
- [ ] Frontend UI saves/loads credentials
- [ ] "Test Connection" buttons work for OpenAI and CCXT
- [ ] AI analysis uses database credentials
- [ ] Live trading uses database credentials
- [ ] Reset to .env functionality works

## Estimated Time to Complete

- **Frontend UI**: 4-6 hours (Settings.jsx extension + API methods)
- **Service Integration**: 2-3 hours (ai_routes, auth, live_engine updates)
- **Documentation**: 1-2 hours (README, CLAUDE.md updates)
- **Testing**: 2-3 hours (full end-to-end validation)

**Total: 9-14 hours** to complete remaining work

## Questions?

Refer to:
1. [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md) - Detailed implementation guide
2. [C:\Users\FaryHuo\.claude\plans\lovely-wondering-journal.md](C:\Users\FaryHuo\.claude\plans\lovely-wondering-journal.md) - Original plan
3. API endpoint documentation in IMPLEMENTATION_SUMMARY.md

---

**Last Updated**: 2025-12-16
**Backend Status**: ✅ Complete (100%)
**Frontend Status**: ⏳ Pending (0%)
**Integration Status**: ⏳ Pending (0%)
