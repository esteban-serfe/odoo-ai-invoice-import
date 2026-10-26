import logging

from odoo import SUPERUSER_ID, api
from odoo.addons.llm_litellm_responses import PROVIDER_NAME

from . import models, wizard  # noqa: F401

_logger = logging.getLogger(__name__)


def post_init_hook(cr, registry):
    """Wire a LiteLLM model onto the invoice_extraction assistant, so a
    fresh install works out of the box - if one is already available.

    llm_litellm_responses's own post_init_hook only auto-provisions the
    LiteLLM provider itself, not a specific model (model selection
    is a deliberate manual step via the LLM > Configuration > Providers > Fetch Models
    wizard). On a fresh install there is usually no model yet, in which
    case this just logs and skips - an admin can assign one to the
    "Invoice Extraction" assistant afterwards (LLM -> Configuration ->
    Assistants), or re-run this hook via a module upgrade once a model has
    been fetched.
    """
    env = api.Environment(cr, SUPERUSER_ID, {})

    provider = (
        env["llm.provider"].sudo().search([("name", "=", PROVIDER_NAME)], limit=1)
    )
    if not provider:
        _logger.warning(
            "LiteLLM provider not found; skipping invoice_extraction "
            "assistant wiring. Ensure llm_litellm_responses's "
            "post_init_hook ran (requires LITELLM_API_BASE and "
            "LITELLM_API_KEY at install time)."
        )
        return

    model = env["llm.model"].sudo().search([("provider_id", "=", provider.id)], limit=1)
    if not model:
        _logger.warning(
            "No LiteLLM model found for provider '%s' yet; skipping "
            "invoice_extraction assistant wiring. Fetch a model via "
            "LLM > Configuration > Providers > LiteLLM > Fetch Models, "
            "then assign it to the 'Invoice Extraction' assistant "
            "manually, or upgrade this module again.",
            provider.name,
        )
        return

    assistant = (
        env["llm.assistant"]
        .sudo()
        .search([("code", "=", "invoice_extraction")], limit=1)
    )
    if not assistant:
        _logger.warning(
            "invoice_extraction assistant not found; LiteLLM model was " "not assigned."
        )
        return

    assistant.write({"model_id": model.id})
    _logger.info(
        "Auto-configured LiteLLM model '%s' for invoice_extraction", model.name
    )
