from odoo import models


class ResCompany(models.Model):
    _inherit = "res.company"

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
        if "l10n_ar_company_requires_vat" in self._fields:
            return not self.l10n_ar_company_requires_vat
        return super()._cannot_refund_vat()
