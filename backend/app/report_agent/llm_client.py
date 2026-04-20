import json
import logging
import urllib.error
import urllib.request

from ..services.integrations import list_user_integrations

logger = logging.getLogger(__name__)


def call_llm(user_id, system_prompt, user_prompt, *, temperature=0.3, timeout=30):
    """Call user's openai_compatible LLM integration. Returns text or None on failure."""
    try:
        integrations = list_user_integrations(user_id)
    except Exception:
        logger.debug("llm_client: failed listing integrations for user %s", user_id)
        return None

    integration = None
    for integ in integrations:
        if integ.provider_key == "openai_compatible" and getattr(integ, "status", "active") == "active":
            integration = integ
            break

    if integration is None:
        return None

    config_public = integration.config_public or {}
    base_url = config_public.get("base_url")
    model = config_public.get("model")

    secret = {}
    try:
        secret = integration._secret_payload or {}
    except Exception:
        pass
    api_key = secret.get("api_key")

    if not base_url or not api_key or not model:
        logger.debug("llm_client: incomplete config for user %s", user_id)
        return None

    payload = {
        "model": model,
        "temperature": temperature,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    }

    try:
        req = urllib.request.Request(
            url=f"{base_url.rstrip('/')}/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            data=json.dumps(payload).encode("utf-8"),
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = json.loads(resp.read().decode("utf-8"))
        return body.get("choices", [{}])[0].get("message", {}).get("content", "").strip() or None
    except Exception:
        logger.debug("llm_client: request failed for user %s", user_id, exc_info=True)
        return None
