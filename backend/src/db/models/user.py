"""
User Models - SQLAlchemy models for user data persistence.

This module defines database tables for storing:
- User settings and credentials
- Strategy versions
"""

from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, JSON, String, Text, UniqueConstraint

from src.db.models.base import Base, SafeJSON


class UserSettingsModel(Base):
    """
    User Settings Model - Stores user preferences for AI models and prompts.

    Supports both authenticated and anonymous users. Settings are per-user
    with fallback to localStorage on frontend if DB operations fail.
    """
    __tablename__ = "user_settings"

    # Primary key (auto-increment for simpler management)
    id = Column(Integer, primary_key=True, autoincrement=True)

    # User identification (nullable for anonymous users)
    # For authenticated users: Logto 'sub' claim (e.g., "auth0|123456")
    # For anonymous: NULL (single row for all anonymous users)
    user_id = Column(String(255), nullable=True, unique=True, index=True)

    # AI Model Configuration
    # Comma-separated list of model names (e.g., "gpt-5.1,deepseek-v3.1")
    # Max length: 500 chars (supports ~50 models at 10 chars each)
    selected_models = Column(String(500), nullable=False, default="gpt-5.1,deepseek-v3.1")

    # AI Prompt Templates
    code_analysis_prompt = Column(Text, nullable=False, default="Please analyze the following Backtrader strategy code. Explain its logic, potential pitfalls, and suggest improvements:\n\n{code}")
    code_rewrite_prompt = Column(Text, nullable=False, default="Please rewrite and optimize the following Backtrader strategy code to follow best practices and fix potential issues. Return ONLY the python code, no markdown formatting or explanation:\n\n{code}")
    full_strategy_analysis_prompt = Column(Text, nullable=False, default="Please analyze the trading strategy based on the following configurations, source code, performance metrics, the attached equity curve chart, and the recent trading logs.\n\n{contextText}\n\n{metricsText}\n\n{logsText}\n\nProvide a comprehensive assessment including:\n1. Overall Performance: Is it profitable and consistent?\n2. Risk Profile: analysis of drawdowns and volatility.\n3. Strengths & Weaknesses: What is working well and what isn't?\n4. Suggestions: Recommendations for improvement.\n5. Code Analysis: Comments on the strategy logic.\n6. Always return with Chinese.\n7. 不需要对策略代码逻辑进行点评")

    # ========== ENCRYPTED CREDENTIALS ==========
    # Note: All credential fields are encrypted using Fernet encryption
    # Values are stored as base64-encoded ciphertext

    # OpenAI Configuration (encrypted)
    openai_api_key = Column(Text, nullable=True)  # Encrypted API key
    openai_base_url = Column(String(500), nullable=True)  # Base URL (not encrypted)

    # Logto Authentication Configuration (encrypted where sensitive)
    logto_issuer = Column(String(500), nullable=True)  # Issuer URL (not encrypted)
    logto_jwks_uri = Column(String(500), nullable=True)  # JWKS URI (not encrypted)
    logto_audience = Column(String(500), nullable=True)  # Audience (not encrypted)
    logto_required_scopes = Column(String(500), nullable=True)  # Space-separated scopes (not encrypted)
    enable_login = Column(Boolean, nullable=True)  # Enable/disable login (not encrypted)

    # Proxy Configuration (not encrypted - just URLs)
    http_proxy = Column(String(500), nullable=True)
    https_proxy = Column(String(500), nullable=True)

    # Site Configuration (Landing Page)
    # These settings control the content displayed on the landing page
    # Values here take precedence over .env file settings
    site_title = Column(String(255), nullable=True)
    site_description = Column(String(500), nullable=True)
    site_docs_url = Column(String(500), nullable=True)
    site_github_url = Column(String(500), nullable=True)
    site_twitter_url = Column(String(500), nullable=True)
    site_email = Column(String(255), nullable=True)
    site_stats_strategies = Column(String(50), nullable=True)
    site_stats_backtests = Column(String(50), nullable=True)
    site_stats_users = Column(String(50), nullable=True)

    # CCXT Exchange Credentials (JSON field for flexible structure)
    # Structure: {
    #   "binance": {
    #     "paper": {"api_key": "encrypted...", "secret": "encrypted..."},
    #     "live": {"api_key": "encrypted...", "secret": "encrypted..."}
    #   },
    #   "okx": {
    #     "paper": {"api_key": "encrypted...", "secret": "encrypted...", "passphrase": "encrypted..."},
    #     "live": {...}
    #   }
    # }
    ccxt_credentials = Column(JSON, nullable=True)

    # Data Source Configuration
    # Priority order for fetching market data (JSON array)
    # Default: ["yahoo", "database"], can include "eodhd"
    data_source_priority = Column(JSON, nullable=True)
    eodhd_api_key = Column(Text, nullable=True)  # Encrypted API key

    # Timestamps for auditing
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return (
            f"<UserSettings(user_id={self.user_id}, "
            f"models={self.selected_models})>"
        )


class StrategyVersionModel(Base):
    """
    Strategy Version Model - Stores versioned snapshots of strategy code.

    Each save creates a new version record, enabling version history,
    diff comparison, and rollback functionality.
    """
    __tablename__ = "strategy_versions"

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Version identifier (auto-increment per strategy)
    version_number = Column(Integer, nullable=False)

    # Strategy identification
    strategy_name = Column(String(255), nullable=False, index=True)

    # User identification (optional, for multi-user support)
    user_id = Column(String(255), nullable=True, index=True)

    # Version metadata
    commit_message = Column(Text, nullable=True)  # Optional commit message
    code = Column(Text, nullable=False)  # Full code snapshot
    code_hash = Column(String(64), nullable=False)  # SHA-256 hash for change detection

    # Change statistics
    lines_added = Column(Integer, default=0)
    lines_removed = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)

    # Composite unique constraint
    __table_args__ = (
        UniqueConstraint('strategy_name', 'version_number', 'user_id',
                        name='uix_strategy_version'),
    )

    def __repr__(self):
        return (
            f"<StrategyVersion(strategy={self.strategy_name}, "
            f"version={self.version_number}, "
            f"created_at={self.created_at})>"
        )


__all__ = [
    "UserSettingsModel",
    "StrategyVersionModel",
]
