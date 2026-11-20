from odoo import _, api, models
from odoo.exceptions import UserError


class LLMToolModelMethodExecutor(models.Model):
    _inherit = "llm.tool"

    @api.model
    def _get_available_implementations(self):
        # Keep the selection value and XML ID readable on existing databases.
        return super()._get_available_implementations() + [
            ("odoo_model_method_executor", "Odoo Model Method Executor (disabled)"),
        ]

    def odoo_model_method_executor_execute(self, **kwargs):
        raise UserError(_("Arbitrary Odoo method execution is disabled."))
