from odoo.tests.common import TransactionCase


class TestFetchModelsWizard(TransactionCase):
    """Tests the action_confirm() override this module adds via _inherit to
    llm.fetch.models.wizard (defined in the base llm module).
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.provider = cls.env["llm.provider"].create(
            {
                "name": "Test LiteLLM",
                "service": "litellm",
                "api_base": "https://litellm.example.test",
                "api_key": "sk-test",
            }
        )

    def test_action_confirm_transfers_model_info_from_details(self):
        wizard = self.env["llm.fetch.models.wizard"].create(
            {"provider_id": self.provider.id}
        )
        self.env["llm.fetch.models.line"].create(
            {
                "wizard_id": wizard.id,
                "name": "chatgpt-gpt-5.4",
                "model_use": "chat",
                "details": {
                    "id": "chatgpt-gpt-5.4",
                    "model_info": {"mode": "responses"},
                },
            }
        )

        wizard.action_confirm()

        model = self.env["llm.model"].search(
            [("provider_id", "=", self.provider.id), ("name", "=", "chatgpt-gpt-5.4")]
        )
        self.assertEqual(len(model), 1)
        self.assertEqual(model.model_info, {"mode": "responses"})

    def test_action_confirm_without_model_info_leaves_it_unset(self):
        wizard = self.env["llm.fetch.models.wizard"].create(
            {"provider_id": self.provider.id}
        )
        self.env["llm.fetch.models.line"].create(
            {
                "wizard_id": wizard.id,
                "name": "some-other-model",
                "model_use": "chat",
                "details": {"id": "some-other-model"},
            }
        )

        wizard.action_confirm()

        model = self.env["llm.model"].search(
            [("provider_id", "=", self.provider.id), ("name", "=", "some-other-model")]
        )
        self.assertEqual(len(model), 1)
        self.assertFalse(model.model_info)
