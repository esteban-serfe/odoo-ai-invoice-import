import logging
import os

from odoo import SUPERUSER_ID, api

from . import models, utils, wizards  # noqa: F401

_logger = logging.getLogger(__name__)

PROVIDER_NAME = "LiteLLM"


def post_init_hook(cr, registry):
    """Auto-provision the "LiteLLM" llm.provider so any module that depends
    on this one has a working provider without a manual step.

    Reads LITELLM_API_BASE and LITELLM_API_KEY from the environment. If either
    is missing (e.g. a test/CI database), logs a warning and skips instead of
    failing the install; the provider can be created or edited by hand later.
    """
    api_key = os.environ.get("LITELLM_API_KEY")
    api_base = (os.environ.get("LITELLM_API_BASE") or "").rstrip("/")
    if not api_key or not api_base:
        _logger.warning(
            "LITELLM_API_BASE and LITELLM_API_KEY must both be set; skipping "
            "automatic %s provider setup. Create the provider manually "
            "or reinstall this module with both variables set.",
            PROVIDER_NAME,
        )
        return

    env = api.Environment(cr, SUPERUSER_ID, {})

    provider = (
        env["llm.provider"].sudo().search([("name", "=", PROVIDER_NAME)], limit=1)
    )
    provider_values = {
        "name": PROVIDER_NAME,
        "service": "litellm",
        "api_base": api_base,
        "api_key": api_key,
        "company_id": env.company.id,
        "active": True,
    }
    if provider:
        provider.write(provider_values)
    else:
        provider = env["llm.provider"].sudo().create(provider_values)

    _logger.info("Auto-configured %s provider", PROVIDER_NAME)
