/**
 * Settings Constants
 * Default values and available options for the Settings page
 */

export const DEFAULT_SETTINGS = {
    selectedModels: ['gpt-5.1', 'deepseek-v3.1'],
    codeAnalysisPrompt: 'Please analyze the following Backtrader strategy code. Explain its logic, potential pitfalls, and suggest improvements:\n\n{code}',
    codeRewritePrompt: 'Please rewrite and optimize the following Backtrader strategy code to follow best practices and fix potential issues. Return ONLY the python code, no markdown formatting or explanation:\n\n{code}',
    fullStrategyAnalysisPrompt: 'Please analyze the trading strategy based on the following configurations, source code, performance metrics, the attached equity curve chart, and the recent trading logs.\n\n{contextText}\n\n{metricsText}\n\n{logsText}\n\nProvide a comprehensive assessment including:\n1. Overall Performance: Is it profitable and consistent?\n2. Risk Profile: analysis of drawdowns and volatility.\n3. Strengths & Weaknesses: What is working well and what isn\'t?\n4. Suggestions: Recommendations for improvement.\n5. Code Analysis: Comments on the strategy logic.\n6. Always return with Chinese.\n7. 不需要对策略代码逻辑进行点评'
};

export const AVAILABLE_MODELS = [
    { value: 'gpt-5.1', label: 'GPT-5.1' },
    { value: 'gpt-4o', label: 'GPT-4o' },
    { value: 'gpt-4-turbo', label: 'GPT-4 Turbo' },
    { value: 'gpt-3.5-turbo', label: 'GPT-3.5 Turbo' },
    { value: 'deepseek-v3.1', label: 'DeepSeek V3.1' },
    { value: 'gemini-3-pro', label: 'Gemini 3 Pro' }
];

export const DEFAULT_CREDENTIALS = {
    ai_provider: 'openai',
    ai_provider_priority: ['openai', 'minimax', 'gemini', 'claude'],
    ai_provider_configs: {
        openai: { api_key: '', base_url: 'https://api.openai.com/v1', default_model: '' },
        minimax: { api_key: '', base_url: 'https://api.minimaxi.com/anthropic', default_model: 'MiniMax-M2.7' },
        gemini: { api_key: '', base_url: 'https://generativelanguage.googleapis.com/v1beta', default_model: '' },
        claude: { api_key: '', base_url: 'https://api.anthropic.com/v1', default_model: '' }
    },
    openai_api_key: '',
    openai_base_url: '',
    // Server-side JWT validation
    logto_issuer: '',
    logto_jwks_uri: '',
    logto_audience: '',
    logto_required_scopes: '',
    enable_login: false,
    auth_provider: 'none',
    system_auth_allow_registration: false,
    // Frontend OAuth configuration
    logto_endpoint: '',
    logto_app_id: '',
    logto_redirect_uri: '',
    logto_post_logout_redirect_uri: '',
    // Proxy settings
    http_proxy: '',
    https_proxy: '',
    ccxt: {}
};

export const AI_PROVIDERS = [
    { key: 'openai', label: 'OpenAI' },
    { key: 'minimax', label: 'MiniMax' },
    { key: 'gemini', label: 'Gemini' },
    { key: 'claude', label: 'Claude' }
];

export const SUPPORTED_EXCHANGES = [
    { key: 'binance', label: 'Binance', hasPassphrase: false }
];
