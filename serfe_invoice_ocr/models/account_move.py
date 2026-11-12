from odoo import _, fields, models
from odoo.exceptions import UserError


class AccountMove(models.Model):
    _inherit = "account.move"

    llm_ocr_enabled = fields.Boolean(
        compute="_compute_llm_ocr_enabled",
        help=(
            "Whether the invoice_extraction llm.assistant is active. "
            "Drives visibility of the 'Process with AI' button."
        ),
    )

    def _compute_llm_ocr_enabled(self):
        enabled = self.env[
            "account.invoice.import.ocr"
        ]._is_invoice_extraction_enabled()
        for move in self:
            move.llm_ocr_enabled = enabled

    def action_process_with_llm(self):
        """Re-raise apx_account_invoice_import_llm's two guard-clause errors as
        translatable messages before delegating to super().

        apx_account_invoice_import_llm/models/account_move.py raises these two
        as plain Python string literals (not _()-wrapped), so no .po file
        can translate them - see Ticket 0140997. Conditions copied verbatim
        from the pristine method; keep them in sync if that method changes.
        """
        self.ensure_one()
        if self.state != "draft":
            raise UserError(
                _(
                    "Can only process draft invoices. "
                    "This invoice is already posted or cancelled."
                )
            )
        if not self._find_invoice_attachment():
            raise UserError(
                _(
                    "No PDF or image attachment found on this invoice. "
                    "Please attach an invoice document first."
                )
            )
        return super().action_process_with_llm()
