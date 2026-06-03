"""
Authentication manager for the ServiceNow MCP server.
"""

import base64
import json
import logging
import time
from pathlib import Path
from typing import Dict, Optional
from urllib.parse import urlencode

import requests

from servicenow_mcp.utils.config import AuthConfig, AuthType


logger = logging.getLogger(__name__)


class AuthTokenRequired(Exception):
    """Raised when an OAuth (authorization_code) token is needed but not available.

    The skill catches this signal to prompt the user to provide a token via the
    `set_oauth_token` tool.
    """


class AuthManager:
    """
    Authentication manager for ServiceNow API.

    Handles authentication with the ServiceNow API using basic, OAuth
    (client_credentials / password), OAuth authorization_code (refresh token,
    "act as the real user" — for SSO instances) and API key methods.
    """

    def __init__(self, config: AuthConfig, instance_url: str = None):
        self.config = config
        self.instance_url = instance_url
        self.token: Optional[str] = None
        self.token_type: Optional[str] = None
        self.refresh_token: Optional[str] = None
        self.expires_at: float = 0.0
        # Seed refresh token from config / persisted file for the authorization_code flow.
        if config and config.type == AuthType.OAUTH_AUTHORIZATION_CODE and config.oauth:
            self.refresh_token = config.oauth.refresh_token or self._load_persisted_refresh_token()

    # ------------------------------------------------------------------ headers
    def get_headers(self) -> Dict[str, str]:
        """Get the authentication headers for API requests."""
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

        if self.config.type == AuthType.BASIC:
            if not self.config.basic:
                raise ValueError("Basic auth configuration is required")
            auth_str = f"{self.config.basic.username}:{self.config.basic.password}"
            encoded = base64.b64encode(auth_str.encode()).decode()
            headers["Authorization"] = f"Basic {encoded}"

        elif self.config.type == AuthType.OAUTH:
            if not self.token:
                self._get_oauth_token()
            headers["Authorization"] = f"{self.token_type} {self.token}"

        elif self.config.type == AuthType.OAUTH_AUTHORIZATION_CODE:
            headers["Authorization"] = f"{self.token_type or 'Bearer'} {self._valid_access_token()}"

        elif self.config.type == AuthType.API_KEY:
            if not self.config.api_key:
                raise ValueError("API key configuration is required")
            headers[self.config.api_key.header_name] = self.config.api_key.api_key

        return headers

    # ------------------------------------------------ authorization_code helpers
    def _token_url(self) -> str:
        oauth_config = self.config.oauth
        if oauth_config and oauth_config.token_url:
            return oauth_config.token_url
        if not self.instance_url:
            raise ValueError("Instance URL is required for OAuth authentication")
        return f"{self.instance_url.rstrip('/')}/oauth_token.do"

    def authorize_url(self, state: str = "servicenow_mcp") -> str:
        """Build the authorization URL the user opens in a browser (goes through SSO)."""
        oauth_config = self.config.oauth
        if not oauth_config:
            raise ValueError("OAuth configuration is required")
        redirect_uri = oauth_config.redirect_uri or f"{self.instance_url.rstrip('/')}/oauth_redirect.do"
        params = {
            "response_type": "code",
            "client_id": oauth_config.client_id,
            "redirect_uri": redirect_uri,
            "state": state,
        }
        return f"{self.instance_url.rstrip('/')}/oauth_auth.do?{urlencode(params)}"

    def _basic_oauth_header(self) -> Dict[str, str]:
        oauth_config = self.config.oauth
        auth_str = f"{oauth_config.client_id}:{oauth_config.client_secret}"
        encoded = base64.b64encode(auth_str.encode()).decode()
        return {
            "Authorization": f"Basic {encoded}",
            "Content-Type": "application/x-www-form-urlencoded",
        }

    def _store_token_response(self, token_data: Dict) -> None:
        self.token = token_data.get("access_token")
        self.token_type = token_data.get("token_type", "Bearer")
        expires_in = int(token_data.get("expires_in", 1800))
        self.expires_at = time.time() + max(0, expires_in - 60)  # refresh 1 min early
        new_refresh = token_data.get("refresh_token")
        if new_refresh:
            self.refresh_token = new_refresh
            self._persist_refresh_token(new_refresh)

    def exchange_code(self, code: str) -> None:
        """Exchange an authorization code (from the browser/SSO redirect) for tokens."""
        oauth_config = self.config.oauth
        redirect_uri = oauth_config.redirect_uri or f"{self.instance_url.rstrip('/')}/oauth_redirect.do"
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri,
        }
        resp = requests.post(self._token_url(), headers=self._basic_oauth_header(), data=data, timeout=30)
        if resp.status_code != 200:
            raise ValueError(f"Authorization code exchange failed ({resp.status_code}): {resp.text}")
        self._store_token_response(resp.json())

    def set_refresh_token(self, refresh_token: str) -> None:
        """Set a refresh token directly and immediately mint an access token."""
        self.refresh_token = refresh_token
        self._persist_refresh_token(refresh_token)
        self._refresh_access_token()

    def set_access_token(self, access_token: str, token_type: str = "Bearer", expires_in: int = 1800) -> None:
        """Set an access token directly (when the user pastes a short-lived bearer token)."""
        self.token = access_token
        self.token_type = token_type
        self.expires_at = time.time() + max(0, expires_in - 60)

    def _refresh_access_token(self) -> None:
        if not self.refresh_token:
            raise AuthTokenRequired(
                "No OAuth token available. Provide one with set_oauth_token "
                "(authorization_code, refresh_token, or access_token)."
            )
        data = {"grant_type": "refresh_token", "refresh_token": self.refresh_token}
        resp = requests.post(self._token_url(), headers=self._basic_oauth_header(), data=data, timeout=30)
        if resp.status_code != 200:
            raise AuthTokenRequired(
                f"Refresh token grant failed ({resp.status_code}): {resp.text}. "
                "Re-authenticate with set_oauth_token."
            )
        self._store_token_response(resp.json())

    def _valid_access_token(self) -> str:
        if self.token and time.time() < self.expires_at:
            return self.token
        # token missing or expired -> try refresh
        self._refresh_access_token()
        return self.token

    def has_valid_token(self) -> bool:
        """Whether a usable token (or a refresh token to mint one) is available."""
        if self.token and time.time() < self.expires_at:
            return True
        return bool(self.refresh_token)

    # ----------------------------------------------------------- persistence
    def _token_file(self) -> Optional[Path]:
        oauth_config = self.config.oauth if self.config else None
        if oauth_config and oauth_config.token_file:
            return Path(oauth_config.token_file).expanduser()
        return None

    def _persist_refresh_token(self, refresh_token: str) -> None:
        path = self._token_file()
        if not path:
            return
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps({"refresh_token": refresh_token}))
        except Exception as e:  # pragma: no cover - best effort
            logger.warning(f"Could not persist refresh token to {path}: {e}")

    def _load_persisted_refresh_token(self) -> Optional[str]:
        path = self._token_file()
        if not path or not path.is_file():
            return None
        try:
            return json.loads(path.read_text()).get("refresh_token")
        except Exception:
            return None

    # ------------------------------------------------------- legacy OAuth grants
    def _get_oauth_token(self):
        """Get an OAuth token via client_credentials, falling back to password grant."""
        if not self.config.oauth:
            raise ValueError("OAuth configuration is required")
        oauth_config = self.config.oauth
        token_url = self._token_url()
        headers = self._basic_oauth_header()

        logger.info("Attempting client_credentials grant...")
        response = requests.post(token_url, headers=headers, data={"grant_type": "client_credentials"}, timeout=30)
        if response.status_code == 200:
            self._store_token_response(response.json())
            return

        if oauth_config.username and oauth_config.password:
            data_password = {
                "grant_type": "password",
                "username": oauth_config.username,
                "password": oauth_config.password,
            }
            logger.info("Attempting password grant...")
            response = requests.post(token_url, headers=headers, data=data_password, timeout=30)
            if response.status_code == 200:
                self._store_token_response(response.json())
                return

        raise ValueError("Failed to get OAuth token using both client_credentials and password grants.")

    def refresh_token_now(self):
        """Force a token refresh for OAuth authentication."""
        if self.config.type == AuthType.OAUTH:
            self.token = None
            self._get_oauth_token()
        elif self.config.type == AuthType.OAUTH_AUTHORIZATION_CODE:
            self._refresh_access_token()
