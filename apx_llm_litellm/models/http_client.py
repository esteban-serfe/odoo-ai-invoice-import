import json
from urllib.parse import urlsplit

import requests
from requests.exceptions import RequestException

from odoo import _
from odoo.exceptions import UserError


class LiteLLMClient:
    """HTTP client for LiteLLM proxy"""

    def __init__(self, api_key, api_base=None):
        try:
            base = urlsplit(api_base)
            if (
                base.scheme not in ("https", "http")
                or not base.hostname
                or base.username is not None
                or base.password is not None
                or base.query
                or base.fragment
            ):
                raise ValueError
        except ValueError:
            raise UserError(_("Configure a valid HTTP(S) API Base URL.")) from None
        self.api_base = api_base.rstrip("/")
        self.session = requests.Session()
        self.session.headers["Content-Type"] = "application/json"
        if api_key:
            self.session.headers["Authorization"] = f"Bearer {api_key}"

    def _make_request(self, method, endpoint, data=None, stream=False, **kwargs):
        """Make HTTP request to LiteLLM proxy"""
        url = f"{self.api_base}{endpoint}"
        try:
            response = self.session.request(
                method=method,
                url=url,
                json=data if data else None,
                stream=stream,
                timeout=(5, 60),
                allow_redirects=False,
                **kwargs,
            )
            if 300 <= response.status_code < 400:
                raise RequestException(response=response)
            response.raise_for_status()
            return response
        except RequestException as exc:
            if exc.response is not None:
                exc.response.close()
            raise UserError(
                _("The AI request failed. Check the provider configuration and service availability.")
            ) from None

    def chat_completion(self, messages, model, stream=False, **kwargs):
        """Create chat completion"""
        data = {"model": model, "messages": messages, "stream": stream}
        data.update(kwargs)
        response = self._make_request(
            "POST", "/chat/completions", data=data, stream=stream
        )

        if not stream:
            return response.json()
        # The streaming loop lives in its own generator: a `yield` here would
        # turn this whole method into a generator, and the non-streaming
        # `return` above would never reach the caller.
        return self._iter_chat_completion_stream(response)

    def _iter_chat_completion_stream(self, response):
        """Yield the parsed SSE chunks of a streaming chat completion."""
        for line in response.iter_lines():
            if line:
                if line.startswith(b"data: "):
                    line = line[6:]  # Remove "data: " prefix
                if line.strip() == b"[DONE]":
                    break
                try:
                    yield json.loads(line)
                except json.JSONDecodeError:
                    continue

    def create_embeddings(self, texts, model):
        """Create embeddings"""
        # Ensure texts is a list
        if isinstance(texts, str):
            texts = [texts]

        data = {"model": model, "input": texts}
        response = self._make_request("POST", "/embeddings", data=data)
        return response.json()

    def list_models(self):
        """List available models"""
        response = self._make_request("GET", "/models")
        return response.json()
