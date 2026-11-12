"""
Account Journal Extension — Upload button opens the review wizard, vendor
bills only

account_invoice_import's own create_document_from_attachment() (called by
the "Upload" button, on every account.move list - Vendor Bills, Customer
Invoices, etc.) always routes the upload through the vendor-bill OCR/
import pipeline, since it never checks move_type - even a Customer Invoice
upload got created as a vendor bill via account.invoice.import. Override
to only apply that pipeline (and open the wizard for review instead of
creating the invoice immediately) when the upload is actually for a vendor
bill/refund, identified by the "default_move_type" context Odoo's own
Vendor Bills/Refunds actions and journal-dashboard widget already set.

Any other context falls back to Odoo core's own generic, decoder-based
create_document_from_attachment() (account/models/account_journal.py),
which OCA's override otherwise fully replaces regardless of move type -
see Ticket 0141016.

When AI-based invoice import is disabled (invoice_extraction llm.assistant
archived), vendor-bill uploads take that same core-decoder fallback
instead of opening the review wizard, with a heads-up toast explaining
why - the wizard has nothing useful left to do without AI, since no
other parser module (facturx/ubl/simple_pdf) is installed here.
"""

from odoo import Command, _, models

_VENDOR_MOVE_TYPES = ("in_invoice", "in_refund")


class AccountJournal(models.Model):
    _inherit = "account.journal"

    def create_document_from_attachment(self, attachment_ids=None):
        if self.env.context.get("default_move_type") not in _VENDOR_MOVE_TYPES:
            return self._create_document_from_core_decoders(attachment_ids)

        # The review wizard exists specifically to host the AI-OCR
        # fallback (and OCA's own XML parsers, none of which are
        # installed in this deployment) - with AI off there's nothing
        # left for it to do, so skip it and fall back to the same plain
        # decoder-dispatch path non-vendor-bill uploads already use,
        # with a heads-up toast instead of a silent switch.
        if not self.env["account.invoice.import.ocr"]._is_invoice_extraction_enabled():
            action = self._create_document_from_core_decoders(attachment_ids)
            attachments = self.env["ir.attachment"].browse(attachment_ids)
            action["context"] = {
                **(action.get("context") or {}),
                # Same "notifications" context key Odoo core's own
                # AccountFileUploader.onUploadComplete() already reads
                # (bills_upload.js) and shows as an info toast.
                "notifications": {
                    attachment.name: _(
                        "AI-based data extraction is currently disabled - "
                        "uploading the file. Please review and complete "
                        "the invoice manually."
                    )
                    for attachment in attachments
                },
            }
            return action

        company_id = self.company_id.id if self else self.env.company.id
        wiz = self.env["account.invoice.import"].create(
            {
                "company_id": company_id,
                "invoice_attachment_ids": [Command.set(attachment_ids)],
            }
        )
        return {
            "type": "ir.actions.act_window",
            "res_model": "account.invoice.import",
            "res_id": wiz.id,
            "views": [[False, "form"]],
            "view_mode": "form",
            "target": "new",
        }

    def _create_document_from_core_decoders(self, attachment_ids):
        """Reproduces Odoo core's own create_document_from_attachment()
        (account/models/account_journal.py) - unreachable via super() since
        OCA's account_invoice_import override replaces it outright without
        calling super(). _create_document_from_attachment() itself (the
        decoder-dispatch logic) is untouched by OCA, so it's called
        directly here rather than duplicated.
        """
        invoices = self._create_document_from_attachment(attachment_ids)
        action_vals = {
            "name": _("Generated Documents"),
            "domain": [("id", "in", invoices.ids)],
            "res_model": "account.move",
            "type": "ir.actions.act_window",
            "context": self._context,
        }
        if len(invoices) == 1:
            action_vals.update(
                {
                    "views": [[False, "form"]],
                    "view_mode": "form",
                    "res_id": invoices[0].id,
                }
            )
        else:
            action_vals.update(
                {
                    "views": [[False, "list"], [False, "kanban"], [False, "form"]],
                    "view_mode": "list, kanban, form",
                }
            )
        return action_vals
