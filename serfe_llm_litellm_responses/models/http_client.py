import json

from odoo.addons.apx_llm_litellm.models.http_client import LiteLLMClient


class LiteLLMResponsesClient(LiteLLMClient):
    """LiteLLMClient extended with the Responses API endpoints the LiteLLM
    deployment needs for chatgpt-5.x models, kept as a subclass so the
    vendored apx_llm_litellm module stays untouched.
    """

    def chat_completion(self, messages, model, stream=False, **kwargs):
        """Same as the vendored chat_completion(), except a non-streaming
        call actually returns the parsed dict instead of a generator.

        The vendored method has a `yield` in its streaming branch, which
        makes Python treat the *whole* method as a generator function -
        including the `if not stream: return response.json()` branch, whose
        `return` then just stops an unconsumed generator instead of handing
        back the dict. Splitting the streaming branch into its own
        generator method avoids that.
        """
        data = {"model": model, "messages": messages, "stream": stream}
        data.update(kwargs)
        response = self._make_request(
            "POST", "/chat/completions", data=data, stream=stream
        )

        if not stream:
            return response.json()
        return self._iter_chat_completion_stream(response)

    def _iter_chat_completion_stream(self, response):
        """Yield parsed SSE chunks for a streaming chat completion response."""
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

    def get_model_info(self):
        """List configured models with their LiteLLM model_info (e.g. "mode").

        Unlike list_models()'s plain OpenAI-compatible /models, this hits the
        LiteLLM-proxy-specific /model/info endpoint, the only one that
        exposes the model_info block (mode, cost, etc.) declared in
        litellm_config.yaml for each model_name.
        """
        response = self._make_request("GET", "/model/info")
        return response.json()

    def create_response(self, input, model, **kwargs):
        """Create a model response via the Responses API endpoint.

        Some LiteLLM-proxied providers (e.g. the "chatgpt" custom provider)
        leave the final response.completed object's "output" empty and only
        emit the actual text through streamed SSE events, so this always
        streams internally and aggregates the text regardless of what the
        caller passes.
        """
        data = {"model": model, "input": input}
        data.update({k: v for k, v in kwargs.items() if k != "stream"})
        data["stream"] = True
        response = self._make_request("POST", "/responses", data=data, stream=True)
        return self._aggregate_response_text(response)

    def _aggregate_response_text(self, response):
        """Consume a Responses API SSE stream and return the assembled output text."""
        text_parts = []
        for line in response.iter_lines():
            if not line:
                continue
            if line.startswith(b"data: "):
                line = line[6:]
            if line.strip() == b"[DONE]":
                break
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            if event.get("type") == "response.output_text.done":
                text_parts.append(event.get("text", ""))
        return "".join(text_parts)
