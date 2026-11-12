from odoo import models


class IrHttp(models.AbstractModel):
    _inherit = "ir.http"

    def session_info(self):
        result = super().session_info()
        # Read by static/src/models/chatter.js to show the chatter "AI" button
        # only to the "User: LLM Chatter" group; the real restriction is the
        # llm.thread ACL, this just avoids showing a button that would fail.
        result["llm_chatter_user"] = self.env.user.has_group(
            "serfe_llm_access_groups.group_llm_chatter_user"
        )
        return result
