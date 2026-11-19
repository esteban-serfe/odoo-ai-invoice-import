"""OCR and chat calls of the "AI Service" provider. Only the HTTP transport
(requests.Session.request) is mocked, so the real provider and client code run.
"""

import json
from unittest.mock import MagicMock, patch

from odoo.tests.common import TransactionCase


def _fake_responses_sse(text):
    lines = [
        b'data: {"type": "response.created"}',
        (
            'data: {"type": "response.output_text.done", "text": %s}' % json.dumps(text)
        ).encode(),
        b'data: {"type": "response.completed", "response": {"output": []}}',
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


class TestLLMProvider(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.provider = cls.env["llm.provider"].create(
            {
                "name": "Test AI",
                "service": "litellm",
                "api_base": "https://ai.example.test",
                "api_key": "sk-test",
            }
        )
        cls.model = cls.env["llm.model"].create(
            {"name": "test-model", "provider_id": cls.provider.id, "model_use": "chat"}
        )

    @patch("requests.Session.request")
    def test_ocr_pdf_uses_input_file(self, mock_request):
        mock_request.return_value = _fake_responses_sse("transcribed text")

        result = self.provider.litellm_process_ocr(
            self.model.name, data=b"%PDF-1.4 fake", mimetype="application/pdf"
        )

        self.assertEqual(result, "transcribed text")
        self.assertEqual(
            mock_request.call_args.kwargs["url"], "https://ai.example.test/responses"
        )
        sent = mock_request.call_args.kwargs["json"]
        self.assertEqual(sent["model"], "test-model")
        file_part = sent["input"][0]["content"][1]
        self.assertEqual(file_part["type"], "input_file")
        self.assertTrue(
            file_part["file_data"].startswith("data:application/pdf;base64,")
        )

    @patch("requests.Session.request")
    def test_ocr_image_uses_input_image(self, mock_request):
        mock_request.return_value = _fake_responses_sse("transcribed text")

        self.provider.litellm_process_ocr(
            self.model.name, data=b"\x89PNG fake", mimetype="image/png"
        )

        file_part = mock_request.call_args.kwargs["json"]["input"][0]["content"][1]
        self.assertEqual(file_part["type"], "input_image")
        self.assertTrue(file_part["image_url"].startswith("data:image/png;base64,"))

    @patch("requests.Session.request")
    def test_non_streaming_chat_returns_dict(self, mock_request):
        """The invoice extraction calls chat with stream=False and expects a
        dict, not a generator (fixed in apx_llm_litellm, see UPSTREAM.md).
        """
        mock_request.return_value = _fake_json_response(
            {"choices": [{"message": {"role": "assistant", "content": "hi there"}}]}
        )

        result = self.model.chat([], stream=False)

        self.assertEqual(result, {"role": "assistant", "content": "hi there"})
        self.assertIn("/chat/completions", mock_request.call_args.kwargs["url"])

    @patch("requests.Session.request")
    def test_chat_sends_prepend_messages_with_plain_system_content(self, mock_request):
        """The assistant's prompt comes as prepend_messages with list content.
        It must be sent, and the system message as a string: some backends
        reject a list there with "System messages are not allowed".
        """
        mock_request.return_value = _fake_json_response(
            {"choices": [{"message": {"role": "assistant", "content": "ok"}}]}
        )
        prepend = [
            {"role": "system", "content": [{"type": "text", "text": "Be brief."}]},
            {"role": "user", "content": [{"type": "text", "text": "Hi"}]},
        ]

        self.model.chat([], stream=False, prepend_messages=prepend)

        sent = mock_request.call_args.kwargs["json"]["messages"]
        self.assertEqual(sent[0], {"role": "system", "content": "Be brief."})
        self.assertEqual(sent[1], prepend[1])

    def test_service_is_labelled_ai_service(self):
        services = dict(self.env["llm.provider"]._get_available_services())
        self.assertEqual(services["litellm"], "AI Service")

    def test_default_provider_is_shipped(self):
        provider = self.env.ref("serfe_invoice_ocr.llm_provider_ai")
        self.assertEqual(provider.service, "litellm")
