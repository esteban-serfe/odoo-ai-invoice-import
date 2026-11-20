from odoo.tests.common import TransactionCase


class TestModuleInstalled(TransactionCase):
    """Only dependency states are asserted here, not this module's own
    state: at the point these tests run (during this module's own install),
    ir.module.module for serfe_invoice_ocr itself is still "to install" -
    Odoo only flips it to "installed" after the loading step finishes, not
    before its tests execute. Dependencies, on the other hand, are already
    fully installed by the time this module's tests run.
    """

    def _get_module_state(self, module_name):
        module = self.env["ir.module.module"].search(
            [("name", "=", module_name)], limit=1
        )
        return module.state

    def test_account_invoice_import_llm_dependency_is_installed(self):
        self.assertEqual(
            self._get_module_state("apx_account_invoice_import_llm"), "installed"
        )

    def test_llm_litellm_dependency_is_installed(self):
        self.assertEqual(self._get_module_state("apx_llm_litellm"), "installed")

    def test_argentine_localization_is_installed(self):
        self.assertEqual(self._get_module_state("l10n_ar"), "installed")

    def test_exactly_one_invoice_extraction_assistant(self):
        """Guards against data/invoice_extraction_assistant_data.xml
        accidentally creating a second llm.assistant with the same code
        instead of patching apx_account_invoice_import_llm's existing record -
        get_assistant_by_code()'s limit=1 search would then pick one of the
        two arbitrarily.
        """
        assistants = self.env["llm.assistant"].search(
            [("code", "=", "invoice_extraction")]
        )
        self.assertEqual(len(assistants), 1)
