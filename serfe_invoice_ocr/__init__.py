import logging

from odoo import SUPERUSER_ID, api

from . import models, wizard  # noqa: F401

_logger = logging.getLogger(__name__)

PROVIDER_NAME = "Proveedor de IA"


def post_init_hook(cr, registry):
    """Set a model of the "Proveedor de IA" provider on the invoice_extraction
    assistant, so a fresh install works out of the box if a model is already
    available.

    On a fresh install the provider has no API settings nor models yet, so
    this only logs and skips: the admin fills in the provider, fetches its
    models and assigns one to the "Invoice Extraction" assistant (LLM ->
    Configuration -> Assistants).
    """
    env = api.Environment(cr, SUPERUSER_ID, {})

    provider = env.ref("serfe_invoice_ocr.llm_provider_ai", raise_if_not_found=False)
    if not provider:
        _logger.warning(
            "'%s' provider not found; skipping invoice_extraction assistant "
            "wiring. Create an 'AI Service' provider (LLM > Configuration > "
            "Providers), fetch its models and assign one to the assistant.",
            PROVIDER_NAME,
        )
        return

    model = env["llm.model"].sudo().search([("provider_id", "=", provider.id)], limit=1)
    if not model:
        _logger.warning(
            "No model found for provider '%s' yet; skipping invoice_extraction "
            "assistant wiring. Fill in its API Base and API Key, press Fetch "
            "Models (LLM > Configuration > Providers), then assign a model to "
            "the 'Invoice Extraction' assistant.",
            provider.name,
        )
        return

    assistant = (
        env["llm.assistant"]
        .sudo()
        .search([("code", "=", "invoice_extraction")], limit=1)
    )
    if not assistant:
        _logger.warning("invoice_extraction assistant not found; no model assigned.")
        return

    assistant.write({"model_id": model.id})
    _logger.info("Auto-configured model '%s' for invoice_extraction", model.name)
