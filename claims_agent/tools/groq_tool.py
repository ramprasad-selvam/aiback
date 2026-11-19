from __future__ import annotations

import json
import logging
import os
import urllib.error
import urllib.request

logger = logging.getLogger(__name__)


class GroqExtractorTool:
    """Tool adapter for conservative LLM-assisted claim extraction."""

    def extract(self, raw_text: str, api_key: str | None, model: str) -> dict | None:
        key = api_key or os.getenv("GROQ_API_KEY")
        if not key:
            logger.warning("Groq extraction skipped: GROQ_API_KEY is not configured")
            return None

        logger.info("Groq extraction starting: model=%s", model)
        prompt = (
            "Extract only values explicitly present in the claim. Never infer values. "
            "Return valid JSON with claim_id, patient_id, provider_name, invoice_number, "
            "date_of_service, total_claimed_amount, icd_codes, and line_items. "
            "Use null for unknown strings and [] for unknown arrays.\n\n" + raw_text
        )
        body = json.dumps({
            "model": model,
            "temperature": 0,
            "response_format": {"type": "json_object"},
            "messages": [{"role": "user", "content": prompt}],
        }).encode()
        request = urllib.request.Request(
            "https://api.groq.com/openai/v1/chat/completions",
            data=body,
            headers={
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
                "User-Agent": "claims-agent-example/1.0",
                "Accept": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                status = getattr(response, "status", 200)
                payload = json.loads(response.read().decode("utf-8"))
            logger.info("Groq API response received: HTTP %s", status)
            parsed = json.loads(payload["choices"][0]["message"]["content"])
            if not isinstance(parsed, dict):
                return None
            logger.info("Groq extraction completed successfully")
            return parsed
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")[:300]
            logger.error("Groq API HTTP error: status=%s detail=%s", exc.code, detail)
        except urllib.error.URLError as exc:
            logger.error("Groq API network error: %s", exc.reason)
        except (json.JSONDecodeError, KeyError, IndexError, TypeError, ValueError) as exc:
            logger.error("Groq response parsing error: %s", exc.__class__.__name__)
        return None
