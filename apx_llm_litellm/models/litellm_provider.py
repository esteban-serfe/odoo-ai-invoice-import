import json

from odoo import api, models

from .http_client import LiteLLMClient


class LLMProvider(models.Model):
    _inherit = "llm.provider"

    def litellm_format_messages(self, messages, system_prompt=None):
        """Convert Odoo messages to the JSON shape expected by LiteLLM."""
        formatted = []
        if system_prompt:
            formatted.append({"role": "system", "content": str(system_prompt)})

        for message in messages or []:
            if isinstance(message, dict):
                values = message.copy()
            else:
                values = {
                    "role": getattr(message, "llm_role", None) or "user",
                    "content": getattr(message, "body", "") or "",
                }
                body_json = getattr(message, "body_json", None) or {}
                if values["role"] == "tool":
                    values["content"] = json.dumps(
                        body_json.get("result", body_json), default=str
                    )
                    tool_call_id = body_json.get("tool_call_id")
                    if tool_call_id:
                        values["tool_call_id"] = tool_call_id
                elif values["role"] == "assistant":
                    tool_calls = body_json.get("tool_calls")
                    if tool_calls:
                        values["tool_calls"] = tool_calls

            role = values.get("role") or "user"
            content = values.get("content", "")
            if isinstance(content, (list, tuple)):
                content = list(content)
            elif not isinstance(content, (str, dict)):
                content = str(content)

            item = {"role": role, "content": content}
            for key in ("name", "tool_call_id", "tool_calls"):
                if values.get(key) is not None:
                    item[key] = values[key]
            formatted.append(item)

        return formatted

    def litellm_format_tools(self, tools):
        """Format Odoo tools as OpenAI-compatible function definitions."""
        formatted = []
        for tool in tools or []:
            schema = tool.input_schema
            if schema:
                try:
                    schema = json.loads(schema)
                except (TypeError, json.JSONDecodeError):
                    schema = None
            schema = schema or tool.get_input_schema() or {
                "type": "object",
                "properties": {},
                "required": [],
            }
            formatted.append(
                {
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description or "",
                        "parameters": {
                            "type": "object",
                            "properties": schema.get("properties", {}),
                            "required": schema.get("required", []),
                        },
                    },
                }
            )
        return formatted

    def action_push_models(self):
        """Open the push models wizard"""
        self.ensure_one()

        # Return action to open wizard
        return {
            "type": "ir.actions.act_window",
            "name": "Push Models to LiteLLM",
            "res_model": "llm.push.models.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "active_id": self.id,
                "active_model": self._name,
            },
        }

    @api.model
    def _get_available_services(self):
        services = super()._get_available_services()
        return services + [("litellm", "LiteLLM Proxy")]

    def litellm_get_client(self):
        """Get LiteLLM client instance"""
        return LiteLLMClient(
            api_key=self.api_key,
            api_base=self.api_base,
        )

    def litellm_chat(self, messages, model=None, stream=False, **kwargs):
        """Send chat messages using LiteLLM proxy"""
        model = self.get_model(model, "chat")
        messages = self.litellm_format_messages(messages)
        # The assistant's prompt (system instructions, and the whole request
        # for one-shot calls such as the invoice extraction) comes here.
        prepend_messages = kwargs.get("prepend_messages")
        if prepend_messages and isinstance(prepend_messages, list):
            messages = prepend_messages + messages
        messages = [self._litellm_flatten_system_content(m) for m in messages]
        tools = kwargs.get("tools")
        params = {
            "messages": messages,
            "model": model.name,
            "stream": stream,
        }
        if tools:
            params["tools"] = self.litellm_format_tools(tools)
            params["tool_choice"] = kwargs.get("tool_choice", "auto")

        # Send chat request
        response = self.client.chat_completion(**params)

        if not stream:
            choice = response["choices"][0]["message"]
            result = {"role": choice["role"], "content": choice.get("content")}
            if choice.get("tool_calls"):
                result["tool_calls"] = choice["tool_calls"]
            return result
        # Streaming lives in its own generator so that a non-streaming call
        # returns the dict above instead of a generator.
        return self._litellm_stream_chat(response)

    @staticmethod
    def _litellm_flatten_system_content(message):
        """Send a text-only system message as a plain string.

        Prompts build every message with a list of content parts. Some
        OpenAI-compatible backends only accept a string for the system role
        (e.g. they map it to the request instructions) and reject the list
        with "System messages are not allowed".
        """
        content = message.get("content")
        if message.get("role") != "system" or not isinstance(content, list):
            return message
        if not all(
            isinstance(part, dict) and part.get("type") == "text" for part in content
        ):
            return message
        return {**message, "content": "\n\n".join(p.get("text", "") for p in content)}

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

    def litellm_embedding(self, texts, model=None):
        """Generate embeddings using LiteLLM proxy"""
        model = self.get_model(model, "embedding")

        response = self.client.create_embeddings(texts=texts, model=model.name)
        return [data["embedding"] for data in response["data"]]

    def litellm_models(self, model_id=None):
        """List available LiteLLM models"""
        response = self.client.list_models()

        for model in response.get("data", []):
            model_id = model.get("id")
            if not model_id:
                continue

            # Determine capabilities from model properties
            capabilities = ["chat"]  # Default capability
            if "embed" in model_id.lower():
                capabilities = ["embedding"]
            elif any(
                kw in model_id.lower() for kw in ["vision", "image", "multimodal"]
            ):
                capabilities = ["chat", "multimodal"]

            yield {
                "name": model_id,
                "details": {
                    "id": model_id,
                    "capabilities": capabilities,
                    "owned_by": model.get("owned_by"),
                    "permissions": model.get("permission", []),
                },
            }
