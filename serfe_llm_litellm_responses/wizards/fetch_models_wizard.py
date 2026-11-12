from odoo import models


class FetchModelsWizard(models.TransientModel):
    _inherit = "llm.fetch.models.wizard"

    def action_confirm(self):
        """Also transfer a provider-supplied details.model_info sub-key
        (e.g. Responses-API "mode") onto llm.model.model_info - the
        vendored wizard only copies the fields it already knows about
        (name, provider_id, model_use, details).
        """
        result = super().action_confirm()

        model_obj = self.env["llm.model"]
        for line in self.line_ids.filtered(
            lambda record: record.selected and record.name
        ):
            model_info = (line.details or {}).get("model_info")
            if not model_info:
                continue
            model = model_obj.search(
                [
                    ("provider_id", "=", self.provider_id.id),
                    ("name", "=", line.name.strip()),
                ],
                limit=1,
            )
            if model:
                model.write({"model_info": model_info})

        return result
