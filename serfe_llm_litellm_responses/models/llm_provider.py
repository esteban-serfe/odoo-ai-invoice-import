import base64
import logging
import time

from odoo import models

from ..utils.litellm_message_validator import LiteLLMMessageValidator
from .http_client import LiteLLMResponsesClient

_logger = logging.getLogger(__name__)

# The "chatgpt" custom provider intermittently rejects a valid PDF/image
# upload with HTTP 400 "invalid_file" ("badly formatted or corrupted"); the
# exact same bytes go through on a retry. LiteLLM never retries a 400, and
# the base client collapses it to a bare Exception, so match on the message.
_OCR_RETRYABLE_MARKERS = ("invalid_file", "badly formatted or corrupted")
_OCR_MAX_ATTEMPTS = 3


class LLMProvider(models.Model):
    _inherit = "llm.provider"

    def litellm_format_messages(self, messages, system_prompt=None):
        """Strip messages the vendored formatter can leave orphaned (e.g. a
        tool response whose assistant tool_calls message fell outside
        llm.thread's history window), which LiteLLM's Responses-API bridge
        rejects as "No tool call found for function call output".
        """
        formatted = super().litellm_format_messages(
            messages, system_prompt=system_prompt
        )
        return LiteLLMMessageValidator(formatted, logger=_logger).validate_and_clean()

    def litellm_get_client(self):
        """Use the Responses-API-capable client instead of the vendored one."""
        return LiteLLMResponsesClient(
            api_key=self.api_key,
            api_base=self.api_base,
        )

    def litellm_chat(self, messages, model=None, stream=False, **kwargs):
        """Send chat messages using LiteLLM proxy, routing chatgpt-5.x
        "responses" models through the Responses API - except when tools
        are present, since /responses only accepts OpenAI's built-in tool
        types (image_generation, shell, file_search), not our
        function-calling tools. LiteLLM's own "chatgpt" provider already
        translates /chat/completions calls (tools included) to the
        upstream Responses API, so tool-bearing calls go through there
        instead.

        This overrides (rather than extends via super()) the vendored
        apx_llm_litellm implementation, which always returns a generator even
        for stream=False - here a non-streaming call returns the result
        dict directly, which the rest of this module (and its callers)
        rely on.
        """
        model = self.get_model(model, "chat")
        tools = kwargs.get("tools")

        if not tools and (model.model_info or {}).get("mode") == "responses":
            return self._litellm_chat_responses_mode(
                model, messages, stream=stream, **kwargs
            )

        params = self._prepare_chat_params_base(
            model,
            messages,
            stream,
            tools=tools,
            prepend_messages=kwargs.get("prepend_messages"),
        )
        if tools:
            params["tool_choice"] = kwargs.get("tool_choice", "auto")

        response = self.client.chat_completion(**params)

        if not stream:
            choice = response["choices"][0]["message"]
            result = {"role": choice["role"], "content": choice.get("content")}
            if choice.get("tool_calls"):
                result["tool_calls"] = choice["tool_calls"]
            return result
        return self._litellm_stream_chat(response)

    def _litellm_stream_chat(self, response):
        """Yield incremental chat results for a streaming chat completion."""
        tool_calls = {}
        for chunk in response:
            delta = chunk["choices"][0].get("delta", {})
            if "content" in delta and delta["content"]:
                yield {"role": "assistant", "content": delta["content"]}
            for tool_call in delta.get("tool_calls", []):
                index = tool_call.get("index", 0)
                current = tool_calls.setdefault(
                    index,
                    {
                        "id": "",
                        "type": "function",
                        "function": {"name": "", "arguments": ""},
                    },
                )
                current["id"] = tool_call.get("id") or current["id"]
                current["type"] = tool_call.get("type") or current["type"]
                function = tool_call.get("function") or {}
                current["function"]["name"] += function.get("name") or ""
                current["function"]["arguments"] += function.get("arguments") or ""
        if tool_calls:
            yield {"tool_calls": list(tool_calls.values())}

    def _litellm_responses_format_input(self, messages):
        """Convert Chat-Completions-style content parts (type: "text") into
        the Responses API's part types ("input_text" for non-assistant
        roles, "output_text" for the assistant role). String content is
        left as-is.
        """
        converted = []
        for message in messages:
            content = message.get("content")
            if isinstance(content, list):
                text_type = (
                    "output_text"
                    if message.get("role") == "assistant"
                    else "input_text"
                )
                content = [
                    {**part, "type": text_type} if part.get("type") == "text" else part
                    for part in content
                ]
                message = {**message, "content": content}
            converted.append(message)
        return converted

    def _litellm_chat_responses_mode(self, model, messages, stream=False, **kwargs):
        """Chat via LiteLLM's own /responses endpoint directly, for
        tool-less calls on models flagged model_info.mode == 'responses'.

        Only reached when there are no tools - litellm_chat() routes any
        tool-bearing call through /chat/completions instead, since this
        path (unlike that one) never learned the Responses API's tool
        schema.
        """
        prepend_messages = kwargs.get("prepend_messages")
        formatted = self.litellm_format_messages(messages)
        input_messages = (
            (prepend_messages + formatted) if prepend_messages else formatted
        )
        input_messages = self._litellm_responses_format_input(input_messages)

        text = self.client.create_response(input=input_messages, model=model.name)
        result = {"role": "assistant", "content": text}
        if not stream:
            return result

        def _single_chunk_stream():
            yield result

        return _single_chunk_stream()

    def litellm_process_ocr(self, model_name, data, mimetype, **kwargs):
        """Transcribe a document to text via the Responses API's file input.

        Sends the raw file as an inline base64 "input_file" (or
        "input_image" for image mimetypes) content part and asks the model
        to transcribe it, since this LiteLLM deployment has no dedicated
        OCR endpoint.
        """
        if isinstance(data, str):
            data = base64.b64decode(data)
        file_b64 = base64.b64encode(data).decode()
        data_uri = f"data:{mimetype};base64,{file_b64}"

        if mimetype.startswith("image/"):
            file_part = {"type": "input_image", "image_url": data_uri}
        else:
            file_part = {
                "type": "input_file",
                "filename": "document.pdf",
                "file_data": data_uri,
            }

        input_messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": (
                            "Transcribe this document to plain text/markdown, "
                            "preserving its structure. Output only the "
                            "transcription, nothing else."
                        ),
                    },
                    file_part,
                ],
            }
        ]

        last_exc = None
        for attempt in range(1, _OCR_MAX_ATTEMPTS + 1):
            try:
                return self.client.create_response(
                    input=input_messages, model=model_name
                )
            except Exception as exc:
                if not any(
                    marker in str(exc).lower() for marker in _OCR_RETRYABLE_MARKERS
                ):
                    raise
                last_exc = exc
                _logger.warning(
                    "OCR upload rejected by provider (attempt %s/%s): %s",
                    attempt,
                    _OCR_MAX_ATTEMPTS,
                    exc,
                )
                if attempt < _OCR_MAX_ATTEMPTS:
                    time.sleep(2 * attempt)
        raise last_exc

    def litellm_models(self, model_id=None):
        """List available LiteLLM models, augmented with model_info (e.g.
        "mode") from LiteLLM's /model/info endpoint, which the vendored
        litellm_models() doesn't have access to.
        """
        model_info_by_name = {}
        try:
            info_response = self.client.get_model_info()
            for entry in info_response.get("data", []):
                name = entry.get("model_name")
                mode = (entry.get("model_info") or {}).get("mode")
                if name and mode:
                    model_info_by_name[name] = {"mode": mode}
        except Exception:
            _logger.warning("Could not fetch model info from LiteLLM", exc_info=True)

        for item in super().litellm_models(model_id=model_id):
            if item["name"] in model_info_by_name:
                item["details"]["model_info"] = model_info_by_name[item["name"]]
            yield item
