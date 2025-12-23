"""
Logto Configuration Mixin - Logto frontend configuration management.

Handles retrieval of Logto configuration for frontend, with fallback to environment variables.
"""

import logging
import os
from typing import Dict, Optional, Any
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class LogtoConfigMixin:
    """Mixin providing Logto frontend configuration methods."""

    def get_logto_frontend_config(
        self,
        user_id: Optional[str] = None,
        db: Optional[Session] = None
    ) -> Dict[str, Any]:
        """
        Get Logto frontend configuration with fallback to environment variables.

        Args:
            user_id: User identifier (for future user-specific configs)
            db: Optional database session

        Returns:
            Dict with Logto configuration:
            - endpoint: Logto server endpoint
            - appId: Logto application (client) ID
            - redirectUri: OAuth redirect URI
            - postLogoutRedirectUri: Post-logout redirect URI
            - enableLogin: Whether login is enabled (false if not configured)
        """
        close_db = False
        if db is None:
            db = self.get_db_session()
            close_db = True

        try:
            # Get individual credentials with fallback
            endpoint, _ = self.get_credential_with_fallback("logto_endpoint", user_id, db)
            app_id, _ = self.get_credential_with_fallback("logto_app_id", user_id, db)
            redirect_uri, _ = self.get_credential_with_fallback("logto_redirect_uri", user_id, db)
            post_logout_redirect_uri, _ = self.get_credential_with_fallback(
                "logto_post_logout_redirect_uri", user_id, db
            )
            enable_login, _ = self.get_credential_with_fallback("enable_login", user_id, db)

            # Fallback to environment variables if database values are None
            if endpoint is None:
                endpoint = os.getenv("LOGTO_ENDPOINT") or os.getenv("VITE_LOGTO_ENDPOINT")
            
            if app_id is None:
                app_id = os.getenv("LOGTO_APP_ID") or os.getenv("VITE_LOGTO_APP_ID")
            
            if redirect_uri is None:
                redirect_uri = os.getenv("LOGTO_REDIRECT_URI") or os.getenv("VITE_LOGTO_REDIRECT_URI")
            
            if post_logout_redirect_uri is None:
                post_logout_redirect_uri = (
                    os.getenv("LOGTO_POST_LOGOUT_REDIRECT_URI") or 
                    os.getenv("VITE_LOGTO_POST_LOGOUT_REDIRECT_URI")
                )
            
            if enable_login is None:
                enable_login_str = os.getenv("ENABLE_LOGIN") or os.getenv("VITE_ENABLE_LOGIN")
                if enable_login_str:
                    enable_login = enable_login_str.lower() not in {"false", "0", "no", "off"}
                else:
                    # If no configuration exists, default to disabled
                    enable_login = False

            # If endpoint or app_id is not configured, disable login
            if not endpoint or not app_id:
                enable_login = False

            return {
                "endpoint": endpoint,
                "appId": app_id,
                "redirectUri": redirect_uri,
                "postLogoutRedirectUri": post_logout_redirect_uri,
                "enableLogin": enable_login if enable_login is not None else False
            }

        except Exception as e:
            logger.error(f"Failed to get Logto frontend config: {e}")
            # Return safe defaults on error - disable login
            return {
                "endpoint": None,
                "appId": None,
                "redirectUri": None,
                "postLogoutRedirectUri": None,
                "enableLogin": False
            }
        finally:
            if close_db:
                db.close()
