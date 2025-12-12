# Frontend Services

This folder contains service modules for interacting with the backend API and other external services.

## File Classification

- **api.js**:
    - Core API configuration (API_URL, authentication token management).
    - Generic HTTP request builders (`buildRequest`, `parseResponse`).
    - Standard CRUD operations and trading-specific API calls (Strategies, Backtesting, Market Data, Live Trading).

- **aiAnalysis.js**:
    - Dedicated service for AI-powered analysis features.
    - Handles AI settings configuration (`getAISettings`, `getAvailableModels`).
    - Implements specific AI workflows:
        - `performFullStrategyAnalysis`: Comprehensive strategy assessment.
        - `analyzeCode`: AI code review and improvement suggestions.
        - `rewriteCode`: AI code refactoring and optimization.
        - `analyzeChart`: Generic entry point for multimodal analysis (text + image).

- **websocket.js**:
    - Manages WebSocket connections for real-time data updates.
    - Handles event subscriptions and message dispatching.

- **aiAnalysis.js**:
    - (Note: ensure no duplication in description if merged or split) - Confirms logic related to AI operations resides here.
