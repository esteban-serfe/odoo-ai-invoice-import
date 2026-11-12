from unittest.mock import patch

from odoo.tests.common import TransactionCase

from .. import PROVIDER_NAME, post_init_hook


class TestPostInitHook(TransactionCase):
    def setUp(self):
        super().setUp()
        # A real LITELLM_API_KEY in the environment makes this module's own
        # post_init_hook auto-create the PROVIDER_NAME provider for real at install
        # time, before any test runs - start each test from a clean slate
        # instead of assuming a pristine database.
        self._find_provider().unlink()

    def _find_provider(self):
        return self.env["llm.provider"].search([("name", "=", PROVIDER_NAME)], limit=1)

    @patch.dict(
        "os.environ",
        {
            "LITELLM_API_KEY": "sk-test",
            "LITELLM_API_BASE": "https://litellm.example.test/",
        },
    )
    def test_creates_provider_from_env(self):
        self.assertFalse(self._find_provider())

        post_init_hook(self.cr, self.registry)

        provider = self._find_provider()
        self.assertTrue(provider)
        self.assertEqual(provider.service, "litellm")
        self.assertEqual(provider.api_key, "sk-test")
        # Trailing slash is stripped.
        self.assertEqual(provider.api_base, "https://litellm.example.test")

    @patch.dict(
        "os.environ",
        {
            "LITELLM_API_KEY": "sk-updated",
            "LITELLM_API_BASE": "https://litellm.example.test",
        },
    )
    def test_updates_existing_provider(self):
        self.env["llm.provider"].create(
            {
                "name": PROVIDER_NAME,
                "service": "litellm",
                "api_base": "https://old.example.test",
                "api_key": "sk-old",
            }
        )

        post_init_hook(self.cr, self.registry)

        providers = self.env["llm.provider"].search([("name", "=", PROVIDER_NAME)])
        self.assertEqual(len(providers), 1)
        self.assertEqual(providers.api_key, "sk-updated")

    @patch.dict(
        "os.environ",
        {"LITELLM_API_KEY": "", "LITELLM_API_BASE": "https://litellm.example.test"},
    )
    def test_skips_without_api_key(self):
        post_init_hook(self.cr, self.registry)

        self.assertFalse(self._find_provider())

    @patch.dict("os.environ", {"LITELLM_API_KEY": "sk-test", "LITELLM_API_BASE": ""})
    def test_skips_without_api_base(self):
        post_init_hook(self.cr, self.registry)

        self.assertFalse(self._find_provider())
