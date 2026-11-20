from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    invoice_ocr_external_processing = fields.Boolean(
        string="Allow external AI invoice processing",
        groups="base.group_system",
        copy=False,
        help="Send complete invoice files, transcriptions, extraction prompts, "
        "company name, CUIT, currency and purchase VAT rates to the configured AI "
        "endpoint. It may forward this data to downstream providers.",
    )

    def _cannot_refund_vat(self):
        """Prefer l10n_ar's AFIP responsibility type over UNECE tax tags.

        account_tax_unece's unece_type_code is never set on l10n_ar taxes, so
        the OCA base check (account_invoice_import/models/res_company.py)
        always concludes an Argentine company can't deduct VAT - which folds
        VAT into the line price instead of keeping it as a real tax line.
        Use l10n_ar_company_requires_vat when available (True only for
        Responsable Inscripto) instead.
        """
        self.ensure_one()
        if self.account_fiscal_country_id.code == "AR":
            return not self.l10n_ar_company_requires_vat
        return super()._cannot_refund_vat()
