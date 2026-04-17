"""OAuth provider utilities for WeChat, GitHub, and Google."""

import urllib.parse
import requests

SUPPORTED_PROVIDERS = {"wechat", "github", "google"}

PROVIDER_CONFIGS = {
    "wechat": {
        "authorize_url": "https://open.weixin.qq.com/connect/qrconnect",
        "token_url": "https://api.weixin.qq.com/sns/oauth2/access_token",
        "userinfo_url": "https://api.weixin.qq.com/sns/userinfo",
    },
    "github": {
        "authorize_url": "https://github.com/login/oauth/authorize",
        "token_url": "https://github.com/login/oauth/access_token",
        "userinfo_url": "https://api.github.com/user",
        "email_url": "https://api.github.com/user/emails",
    },
    "google": {
        "authorize_url": "https://accounts.google.com/o/oauth2/v2/auth",
        "token_url": "https://oauth2.googleapis.com/token",
        "userinfo_url": "https://www.googleapis.com/oauth2/v2/userinfo",
    },
}


def get_oauth_config(app, provider):
    """Return (client_id, client_secret, endpoints) for the given provider."""
    if provider not in SUPPORTED_PROVIDERS:
        raise ValueError(f"Unsupported OAuth provider: {provider}")

    prefix = provider.upper()
    client_id = app.config.get(f"OAUTH_{prefix}_CLIENT_ID", "")
    client_secret = app.config.get(f"OAUTH_{prefix}_CLIENT_SECRET", "")
    endpoints = PROVIDER_CONFIGS[provider]
    return client_id, client_secret, endpoints


def build_authorization_url(app, provider, state, redirect_uri):
    """Build the full authorization URL for the given provider."""
    client_id, _, endpoints = get_oauth_config(app, provider)
    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "state": state,
        "response_type": "code",
    }

    if provider == "wechat":
        params["scope"] = "snsapi_login"
    elif provider == "github":
        params["scope"] = "user:email"
    elif provider == "google":
        params["scope"] = "openid email profile"

    return f"{endpoints['authorize_url']}?{urllib.parse.urlencode(params)}"


def exchange_code_for_token(app, provider, code, redirect_uri):
    """Exchange authorization code for access token. Returns raw token response dict."""
    client_id, client_secret, endpoints = get_oauth_config(app, provider)
    token_url = endpoints["token_url"]

    if provider == "wechat":
        data = {
            "appid": client_id,
            "secret": client_secret,
            "code": code,
            "grant_type": "authorization_code",
        }
    else:
        data = {
            "client_id": client_id,
            "client_secret": client_secret,
            "code": code,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
        }

    headers = {"Accept": "application/json"}
    resp = requests.post(token_url, data=data, headers=headers, timeout=10)
    resp.raise_for_status()
    return resp.json()


def fetch_user_profile(app, provider, access_token, openid=None):
    """Fetch user profile from the OAuth provider. Returns standardized dict."""
    _, _, endpoints = get_oauth_config(app, provider)
    userinfo_url = endpoints["userinfo_url"]

    if provider == "wechat":
        params = {"access_token": access_token, "openid": openid}
        resp = requests.get(userinfo_url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        return {
            "provider_user_id": str(data.get("openid", "")),
            "email": data.get("email", ""),
            "display_name": data.get("nickname", ""),
            "avatar_url": data.get("headimgurl", ""),
            "raw_profile": data,
        }

    if provider == "github":
        headers = {"Authorization": f"Bearer {access_token}", "Accept": "application/json"}
        resp = requests.get(userinfo_url, headers=headers, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        email = data.get("email") or ""
        if not email:
            email_url = endpoints.get("email_url")
            if email_url:
                email_resp = requests.get(email_url, headers=headers, timeout=10)
                if email_resp.ok:
                    for entry in email_resp.json():
                        if entry.get("primary"):
                            email = entry.get("email", "")
                            break

        return {
            "provider_user_id": str(data.get("id", "")),
            "email": email,
            "display_name": data.get("name") or data.get("login", ""),
            "avatar_url": data.get("avatar_url", ""),
            "raw_profile": data,
        }

    # google
    headers = {"Authorization": f"Bearer {access_token}"}
    resp = requests.get(userinfo_url, headers=headers, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    return {
        "provider_user_id": data.get("id", ""),
        "email": data.get("email", ""),
        "display_name": data.get("name", ""),
        "avatar_url": data.get("picture", ""),
        "raw_profile": data,
    }
