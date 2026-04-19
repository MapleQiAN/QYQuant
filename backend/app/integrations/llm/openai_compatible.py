import logging

import requests

logger = logging.getLogger(__name__)

_TIMEOUT = 10


class OpenAICompatibleLLMAdapter:
    def validate_credentials(self, config):
        secret_payload = config.get("secret_payload") or {}
        config_public = config.get("config_public") or {}

        api_key = secret_payload.get("api_key")
        base_url = config_public.get("base_url")
        model = config_public.get("model")

        if not api_key:
            return {"status": "invalid", "message": "API key is required"}
        if not base_url:
            return {"status": "invalid", "message": "Base URL is required"}

        url = f"{base_url.rstrip('/')}/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": model or "gpt-3.5-turbo",
            "messages": [{"role": "user", "content": "hi"}],
            "max_tokens": 1,
        }

        try:
            resp = requests.post(url, json=payload, headers=headers, timeout=_TIMEOUT)
            if resp.status_code == 401:
                return {"status": "invalid", "message": "Invalid API key"}
            if resp.status_code == 404:
                return {"status": "invalid", "message": f"Model '{model}' not found at this endpoint"}
            if resp.status_code >= 400:
                detail = resp.text[:200]
                return {"status": "invalid", "message": f"API error ({resp.status_code}): {detail}"}
            return {"status": "valid", "message": "API key is valid"}
        except requests.ConnectionError:
            return {"status": "invalid", "message": f"Cannot connect to {base_url}"}
        except requests.Timeout:
            return {"status": "invalid", "message": f"Connection timed out to {base_url}"}
        except Exception as exc:
            logger.exception("LLM credential validation failed")
            return {"status": "invalid", "message": str(exc)}
