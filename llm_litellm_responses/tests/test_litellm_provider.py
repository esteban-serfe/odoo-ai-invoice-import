"""Unit tests for the Responses API support this module adds to llm.provider
via _inherit, isolated from any module that consumes it (no invoice import
wizard involved). Only the HTTP transport (requests.Session.request) is
mocked, so the real LiteLLMResponsesClient/llm.provider code runs end to end.
"""

import json
from unittest.mock import MagicMock, patch

import requests
from odoo.tests.common import TransactionCase


def _fake_responses_sse(text):
    lines = [
        b'data: {"type": "response.created"}',
        (
            'data: {"type": "response.output_text.done", "text": %s}' % json.dumps(text)
        ).encode(),
        b"data: [DONE]",
    ]
    fake_response = MagicMock()
    fake_response.iter_lines.return_value = lines
    fake_response.raise_for_status.return_value = None
    return fake_response


def _fake_json_response(payload):
    fake_response = MagicMock()
    fake_response.json.return_value = payload
    fake_response.raise_for_status.return_value = None
    return fake_response


def _fake_error_response(message):
    """A response whose raise_for_status() fails the way the LiteLLM proxy's
    does - so _make_request() collapses it to Exception("LiteLLM API error:
    <message>").
    """
    fake_response = MagicMock()
    err = requests.HTTPError(message)
    err.response = MagicMock()
    err.response.json.side_effect = ValueError("not json")
    fake_response.raise_for_status.side_effect = err
    return fake_response


class _FakeTool:
    """Duck-typed llm.tool stand-in, so this test doesn't need llm_tool as
    a dependency just to exercise litellm_format_tools().
    """

    name = "test_tool"
    description = "A test tool"
    input_schema = None

    def get_input_schema(self):
        return {"type": "object", "properties": {}, "required": []}


class TestLiteLLMProvider(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.provider = cls.env["llm.provider"].create(
            {
                "name": "Test LiteLLM",
                "service": "litellm",
                "api_base": "https://litellm.example.test",
                "api_key": "sk-test",
            }
        )

    def _create_model(self, name="chatgpt-gpt-5.4", model_info=None):
        return self.env["llm.model"].create(
            {
                "name": name,
                "provider_id": self.provider.id,
                "model_use": "chat",
                "model_info": model_info or {},
            }
        )

    @patch("requests.Session.request")
    def test_litellm_chat_routes_to_responses_mode(self, mock_request):
        model = self._create_model(model_info={"mode": "responses"})
        mock_request.return_value = _fake_responses_sse("hello there")

        result = self.provider.litellm_chat(
            [{"role": "user", "content": "hi"}], model=model
        )

        self.assertEqual(result, {"role": "assistant", "content": "hello there"})
        self.assertIn("/responses", mock_request.call_args.kwargs["url"])

    @patch("requests.Session.request")
    def test_litellm_chat_with_tools_uses_chat_completions_despite_responses_mode(
        self, mock_request
    ):
        # /responses only accepts OpenAI's built-in tool types (image
        # generation, shell, file search) - not arbitrary function-calling
        # tools like ours - so a tool-bearing call must go through
        # /chat/completions even when the model is flagged responses mode;
        # LiteLLM's own "chatgpt" provider handles the translation there.
        model = self._create_model(model_info={"mode": "responses"})
        mock_request.return_value = _fake_json_response(
            {"choices": [{"message": {"role": "assistant", "content": "hi there"}}]}
        )

        result = self.provider.litellm_chat(
            [{"role": "user", "content": "hi"}], model=model, tools=[_FakeTool()]
        )

        self.assertEqual(result, {"role": "assistant", "content": "hi there"})
        self.assertIn("/chat/completions", mock_request.call_args.kwargs["url"])

    @patch("requests.Session.request")
    def test_litellm_process_ocr_pdf_uses_input_file(self, mock_request):
        model = self._create_model()
        mock_request.return_value = _fake_responses_sse("transcribed text")

        result = self.provider.litellm_process_ocr(
            model.name, data=b"%PDF-1.4 fake", mimetype="application/pdf"
        )

        self.assertEqual(result, "transcribed text")
        sent = mock_request.call_args.kwargs["json"]
        file_part = sent["input"][0]["content"][1]
        self.assertEqual(file_part["type"], "input_file")
        self.assertTrue(
            file_part["file_data"].startswith("data:application/pdf;base64,")
        )

    @patch("requests.Session.request")
    def test_litellm_process_ocr_image_uses_input_image(self, mock_request):
        model = self._create_model()
        mock_request.return_value = _fake_responses_sse("transcribed text")

        self.provider.litellm_process_ocr(
            model.name, data=b"\x89PNG fake", mimetype="image/png"
        )

        sent = mock_request.call_args.kwargs["json"]
        file_part = sent["input"][0]["content"][1]
        self.assertEqual(file_part["type"], "input_image")
        self.assertTrue(file_part["image_url"].startswith("data:image/png;base64,"))

    @patch("odoo.addons.llm_litellm_responses.models.llm_provider.time.sleep")
    @patch("requests.Session.request")
    def test_litellm_process_ocr_retries_transient_invalid_file(
        self, mock_request, mock_sleep
    ):
        # The chatgpt provider intermittently 400s a valid upload with
        # "invalid_file"; the same bytes go through on a retry.
        model = self._create_model()
        mock_request.side_effect = [
            _fake_error_response(
                "litellm.BadRequestError: ChatgptException - badly formatted "
                "or corrupted ... 'code': 'invalid_file'"
            ),
            _fake_error_response(
                "litellm.BadRequestError: ChatgptException - badly formatted "
                "or corrupted ... 'code': 'invalid_file'"
            ),
            _fake_responses_sse("transcribed text"),
        ]

        result = self.provider.litellm_process_ocr(
            model.name, data=b"%PDF-1.4 fake", mimetype="application/pdf"
        )

        self.assertEqual(result, "transcribed text")
        self.assertEqual(mock_request.call_count, 3)

    @patch("odoo.addons.llm_litellm_responses.models.llm_provider.time.sleep")
    @patch("requests.Session.request")
    def test_litellm_process_ocr_raises_after_exhausting_retries(
        self, mock_request, mock_sleep
    ):
        model = self._create_model()
        mock_request.side_effect = [
            _fake_error_response("ChatgptException - ... 'code': 'invalid_file'")
            for _ in range(3)
        ]

        with self.assertRaises(Exception) as ctx:
            self.provider.litellm_process_ocr(
                model.name, data=b"%PDF-1.4 fake", mimetype="application/pdf"
            )

        self.assertIn("invalid_file", str(ctx.exception))
        self.assertEqual(mock_request.call_count, 3)

    @patch("odoo.addons.llm_litellm_responses.models.llm_provider.time.sleep")
    @patch("requests.Session.request")
    def test_litellm_process_ocr_does_not_retry_other_errors(
        self, mock_request, mock_sleep
    ):
        model = self._create_model()
        mock_request.side_effect = [
            _fake_error_response("Internal Server Error"),
            _fake_responses_sse("should never be reached"),
        ]

        with self.assertRaises(Exception):
            self.provider.litellm_process_ocr(
                model.name, data=b"%PDF-1.4 fake", mimetype="application/pdf"
            )

        self.assertEqual(mock_request.call_count, 1)

    @patch("requests.Session.request")
    def test_litellm_models_includes_model_info_from_model_info_endpoint(
        self, mock_request
    ):
        # This module's litellm_models() calls get_model_info() (its own
        # /model/info addition) before delegating to the vendored
        # list_models()-based loop via super() - hence get_model_info's
        # response goes first here.
        mock_request.side_effect = [
            _fake_json_response(
                {
                    "data": [
                        {
                            "model_name": "chatgpt-gpt-5.4",
                            "model_info": {"mode": "responses"},
                        }
                    ]
                }
            ),
            _fake_json_response(
                {"data": [{"id": "chatgpt-gpt-5.4", "owned_by": "openai"}]}
            ),
        ]

        models = list(self.provider.litellm_models())

        self.assertEqual(len(models), 1)
        self.assertEqual(models[0]["details"]["model_info"], {"mode": "responses"})

    @patch("requests.Session.request")
    def test_litellm_models_survives_model_info_endpoint_failure(self, mock_request):
        mock_request.side_effect = [
            requests.exceptions.RequestException("boom"),
            _fake_json_response(
                {"data": [{"id": "chatgpt-gpt-5.4", "owned_by": "openai"}]}
            ),
        ]

        models = list(self.provider.litellm_models())

        self.assertEqual(len(models), 1)
        self.assertNotIn("model_info", models[0]["details"])

    def test_litellm_format_messages_removes_orphaned_tool_message(self):
        # A tool response whose assistant tool_calls message fell outside
        # llm.thread's history window (e.g. get_llm_messages()'s 25-message
        # cutoff landing mid-pair) must not reach the API: LiteLLM's
        # Responses-API bridge rejects it as "No tool call found for
        # function call output with call_id ...". Without the
        # litellm_format_messages() override this module adds, the
        # vendored formatter passes the orphan through untouched.
        messages = [
            {"role": "user", "content": "hi"},
            {
                "role": "tool",
                "tool_call_id": "call_azYkS3NoscDHMhQ4HNPyIpz6",
                "content": '{"result": "ok"}',
            },
        ]

        formatted = self.provider.litellm_format_messages(messages)

        self.assertFalse(
            any(msg.get("role") == "tool" for msg in formatted),
            "orphaned tool message should have been stripped",
        )

    @patch("requests.Session.request")
    def test_litellm_chat_strips_orphaned_tool_message_before_sending(
        self, mock_request
    ):
        # End-to-end version of the above: drives the same litellm_chat()
        # path a real llm.thread reply uses, and inspects the actual
        # request body that would have gone to LiteLLM.
        model = self._create_model()
        mock_request.return_value = _fake_json_response(
            {"choices": [{"message": {"role": "assistant", "content": "ok"}}]}
        )
        messages = [
            {"role": "user", "content": "hi"},
            {
                "role": "tool",
                "tool_call_id": "call_azYkS3NoscDHMhQ4HNPyIpz6",
                "content": '{"result": "ok"}',
            },
        ]

        self.provider.litellm_chat(messages, model=model)

        sent_messages = mock_request.call_args.kwargs["json"]["messages"]
        self.assertFalse(
            any(msg.get("role") == "tool" for msg in sent_messages),
            "orphaned tool message should not be sent to LiteLLM",
        )
