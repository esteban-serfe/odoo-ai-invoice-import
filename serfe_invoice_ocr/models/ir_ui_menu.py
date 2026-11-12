"""
IR UI Menu Extension — hide "Import Vendor Bills" while AI import is off

Odoo caches `_visible_menu_ids()` per set of user groups, without looking
at anything else, so the invoice_extraction assistant's state is subtracted
here on every call, after the cached result is computed, instead of being
baked into the cache. That keeps the menu in sync with the "Process with AI"
button, which reads the same state live (see
account.move.llm_ocr_enabled), with nothing stored per user.
"""

from odoo import api, models


class IrUiMenu(models.Model):
    _inherit = "ir.ui.menu"

    @api.model
    def _visible_menu_ids(self, debug=False):
        visible = super()._visible_menu_ids(debug)
        if self.env["account.invoice.import.ocr"]._is_invoice_extraction_enabled():
            return visible
        menu = self.env.ref(
            "account_invoice_import.account_invoice_import_menu",
            raise_if_not_found=False,
        )
        if not menu:
            return visible
        # Return a copy: `visible` is the very set Odoo keeps in its cache.
        return visible - {menu.id}
