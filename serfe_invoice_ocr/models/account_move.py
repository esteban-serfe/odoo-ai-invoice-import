from odoo import _, api, fields, models
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

    @api.depends("company_id", "company_id.invoice_ocr_external_processing")
    @api.depends_context("uid", "company")
    def _compute_llm_ocr_enabled(self):
        ocr = self.env["account.invoice.import.ocr"]
        for move in self:
            move.llm_ocr_enabled = ocr._is_invoice_extraction_enabled(move.company_id)

    def action_process_with_llm(self):
        """Keep the button's errors translatable for the Argentine workflow."""
        self.ensure_one()
        self.check_access_rights("write")
        self.check_access_rule("write")
        if self.move_type not in ("in_invoice", "in_refund"):
            raise UserError(_("Only vendor bills and refunds can be processed."))
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
