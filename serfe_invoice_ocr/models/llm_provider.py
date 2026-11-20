import base64
import json

from requests.exceptions import RequestException

from odoo import _, api, models
from odoo.exceptions import UserError

OCR_INSTRUCTIONS = (
    "Transcribe this document to plain text/markdown, preserving its "
    "structure. Output only the transcription, nothing else."
)


class LLMProvider(models.Model):
    _inherit = "llm.provider"

    @api.model
    def _get_available_services(self):
        """Show the "litellm" service as a generic "AI Service". Only the label
        changes: the stored key stays "litellm", so every service dispatch
        keeps working.
        """
        return [
            (key, _("AI Service") if key == "litellm" else label)
            for key, label in super()._get_available_services()
        ]

    def _litellm_process_ocr(self, model_name, data, mimetype):
        """Transcribe a document to text with the provider's Responses API.

        The file goes inline, base64 encoded, as an "input_file" content part
        ("input_image" for images), next to the transcription instructions.
        """
        if isinstance(data, str):
            data = base64.b64decode(data)
        data_uri = f"data:{mimetype};base64,{base64.b64encode(data).decode()}"

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
                "content": [{"type": "input_text", "text": OCR_INSTRUCTIONS}, file_part],
            }
        ]
        return self._litellm_responses_text(input_messages, model_name)

    def _litellm_responses_text(self, input_messages, model_name):
        """POST to /responses and return the generated text.

        Streams and keeps the "response.output_text.done" events: some
        providers leave the final "response.completed" object without output
        and only send the text through those events.
        """
        response = self._litellm_get_client()._make_request(
            "POST",
            "/responses",
            data={"model": model_name, "input": input_messages, "stream": True},
            stream=True,
        )
        text_parts = []
        try:
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
                if event.get("type") in ("error", "response.failed"):
                    raise UserError(_("The AI service could not transcribe the invoice."))
                if event.get("type") == "response.output_text.done":
                    text_parts.append(event.get("text", ""))
        except RequestException:
            raise UserError(_("The AI transcription connection was interrupted.")) from None
        finally:
            response.close()
        return "".join(text_parts)
