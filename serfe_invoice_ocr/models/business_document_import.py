"""
Business Document Import — main attachment fix

OCA's post_create_or_update() attaches the source file to the created/updated
account.move with a bare ir.attachment.create(), so the move never gets a
message_main_attachment_id. The vendor bill form's PDF preview pane binds to
that field, so it stays blank until the user reloads the page. Set it here,
covering both entry points (the OCA import wizard and the "Process with AI"
button), which both funnel through this method.
"""

from odoo import api, models

_PREVIEWABLE_MIMETYPES = ["application/pdf", "image/png", "image/jpeg", "image/jpg"]


class BusinessDocumentImport(models.AbstractModel):
    _inherit = "business.document.import"

    @api.model
    def post_create_or_update(self, parsed_dict, record, doc_filename=None):
        res = super().post_create_or_update(parsed_dict, record, doc_filename)
        if record._name == "account.move" and not record.message_main_attachment_id:
            attachment = self.env["ir.attachment"].search(
                [
                    ("res_model", "=", "account.move"),
                    ("res_id", "=", record.id),
                    ("mimetype", "in", _PREVIEWABLE_MIMETYPES),
                ],
                order="id desc",
                limit=1,
            )
            if attachment:
                record.message_main_attachment_id = attachment.id
        return res
