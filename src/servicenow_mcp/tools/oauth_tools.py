"""
OAuth (authorization_code) session tools for the ServiceNow MCP server.

For SSO instances configured with `oauth_authorization_code`, the token must
represent the real user. The server cannot run an interactive browser flow, so
these tools let the assistant (a skill) drive it:

1. `get_auth_status` — does the current instance need a token right now?
2. `get_oauth_authorize_url` — the URL the user opens in a browser (goes through SSO).
3. `set_oauth_token` — inject the authorization code / refresh token / access token
   the user pasted back, mutating the live AuthManager so subsequent calls act as them.
"""

import logging
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field

from servicenow_mcp.auth.auth_manager import AuthManager
from servicenow_mcp.utils.config import AuthType, ServerConfig

logger = logging.getLogger(__name__)


class GetAuthStatusParams(BaseModel):
    """Parameters for getting auth status (no inputs required)."""

    random_string: Optional[str] = Field(
        None, description="Unused; present so the tool can be called without arguments"
    )


class GetOAuthAuthorizeUrlParams(BaseModel):
    """Parameters for building the OAuth authorize URL."""

    state: str = Field("servicenow_mcp", description="OAuth state parameter")


class SetOAuthTokenParams(BaseModel):
    """Parameters for injecting an OAuth token. Provide exactly one of the three."""

    authorization_code: Optional[str] = Field(
        None, description="Authorization code from the browser/SSO redirect (?code=...)"
    )
    refresh_token: Optional[str] = Field(
        None, description="A refresh token to mint access tokens from"
    )
    access_token: Optional[str] = Field(
        None, description="A short-lived bearer access token to use directly"
    )


class SetOAuthTokenResponse(BaseModel):
    """Response from set_oauth_token."""

    success: bool = Field(..., description="Whether the operation was successful")
    message: str = Field(..., description="Message describing the result")
    token_loaded: bool = Field(False, description="Whether a usable token is now loaded")


def get_auth_status(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: GetAuthStatusParams,
) -> Dict[str, Any]:
    """Report the current auth type and whether a user token is needed now."""
    auth_type = config.auth.type.value if config.auth else None
    is_authcode = config.auth and config.auth.type == AuthType.OAUTH_AUTHORIZATION_CODE

    if not is_authcode:
        return {
            "success": True,
            "auth_type": auth_type,
            "requires_token": False,
            "token_loaded": True,
            "message": f"Instance uses '{auth_type}' auth; no interactive token needed.",
        }

    loaded = auth_manager.has_valid_token()
    result = {
        "success": True,
        "auth_type": auth_type,
        "requires_token": not loaded,
        "token_loaded": loaded,
        "instance_url": config.instance_url,
    }
    if not loaded:
        try:
            result["authorize_url"] = auth_manager.authorize_url()
        except Exception as e:
            result["authorize_url_error"] = str(e)
        result["message"] = (
            "This instance acts as the real user via SSO and needs a token. Open the "
            "authorize_url in a browser, sign in through SSO, then paste the 'code' from "
            "the redirect URL into set_oauth_token (authorization_code=...)."
        )
    else:
        result["message"] = "A valid user token is loaded; you can proceed."
    return result


def get_oauth_authorize_url(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: GetOAuthAuthorizeUrlParams,
) -> Dict[str, Any]:
    """Return the SSO authorize URL for the authorization_code flow."""
    if not (config.auth and config.auth.type == AuthType.OAUTH_AUTHORIZATION_CODE):
        return {
            "success": False,
            "message": "Current instance is not configured for oauth_authorization_code.",
        }
    try:
        return {
            "success": True,
            "authorize_url": auth_manager.authorize_url(params.state),
            "message": "Open this URL in a browser, sign in (SSO), then copy the 'code' "
            "from the redirect URL and call set_oauth_token.",
        }
    except Exception as e:
        return {"success": False, "message": f"Could not build authorize URL: {str(e)}"}


def set_oauth_token(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: SetOAuthTokenParams,
) -> SetOAuthTokenResponse:
    """Inject an OAuth token (code/refresh/access) into the live session."""
    if not (config.auth and config.auth.type == AuthType.OAUTH_AUTHORIZATION_CODE):
        return SetOAuthTokenResponse(
            success=False,
            message="Current instance is not configured for oauth_authorization_code.",
        )
    provided = [p for p in (params.authorization_code, params.refresh_token, params.access_token) if p]
    if len(provided) != 1:
        return SetOAuthTokenResponse(
            success=False,
            message="Provide exactly one of: authorization_code, refresh_token, access_token.",
        )
    try:
        if params.authorization_code:
            auth_manager.exchange_code(params.authorization_code.strip())
        elif params.refresh_token:
            auth_manager.set_refresh_token(params.refresh_token.strip())
        else:
            auth_manager.set_access_token(params.access_token.strip())
        return SetOAuthTokenResponse(
            success=True,
            message="OAuth token loaded; subsequent calls act as the authenticated user.",
            token_loaded=auth_manager.has_valid_token(),
        )
    except Exception as e:
        logger.error(f"Error setting OAuth token: {e}")
        return SetOAuthTokenResponse(success=False, message=f"Error setting OAuth token: {str(e)}")
