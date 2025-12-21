# Response Format Compatibility

When backend authentication is **disabled**, some API endpoints return a different response format:

## Example: `/api/strategies`

### Auth Enabled
```json
[
  "strategy1",
  "strategy2",
  "strategy3"
]
```

### Auth Disabled  
```json
{
  "strategies": [
    "strategy1",
    "strategy2",
    "strategy3"
  ]
}
```

## Solution

Tests now handle both formats automatically using conditional logic to extract the data regardless of auth state.

This ensures tests work seamlessly whether auth is enabled or disabled!
