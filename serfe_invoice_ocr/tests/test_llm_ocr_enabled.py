"""Functional tests for the invoice_extraction assistant's active field
acting as the AI-import enable/disable switch, and everything that
hides/blocks around it.

Deliberately does not assert on error/notification message text -
only on behavior.

Does not duplicate test_invoice_ocr_wizard.py's full mocked-LLM-call
fixtures: these tests only need the invoice_extraction assistant record
itself (already seeded by data/invoice_extraction_assistant_data.xml)
plus, for the menu-visibility tests, res.users.
"""

from odoo.exceptions import UserError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


# Creating vendor bills needs a chart of accounts and journals, which are only
# loaded after the at_install tests of this module have run.
@tagged("post_install", "-at_install")
class TestLlmOcrEnabled(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.assistant = cls.env["llm.assistant"].search(
            [("code", "=", "invoice_extraction")], limit=1
        )
        cls.ocr = cls.env["account.invoice.import.ocr"]
        cls.menu = cls.env.ref("account_invoice_import.account_invoice_import_menu")

    def test_archived_assistant_blocks_extraction(self):
        self.assistant.active = False
        self.assertFalse(self.ocr._is_invoice_extraction_enabled())
        with self.assertRaises(UserError):
            self.ocr._get_invoice_extraction_assistant()

    def test_missing_assistant_blocks_extraction(self):
        self.assistant.code = "not_invoice_extraction_anymore"
        self.assertFalse(self.ocr._is_invoice_extraction_enabled())
        with self.assertRaises(UserError):
            self.ocr._get_invoice_extraction_assistant()

    def test_active_assistant_is_returned(self):
        self.assertTrue(self.ocr._is_invoice_extraction_enabled())
        found = self.ocr._get_invoice_extraction_assistant()
        self.assertEqual(found, self.assistant)

    def test_account_move_llm_ocr_enabled_reflects_assistant_state(self):
        move = self.env["account.move"].create({"move_type": "in_invoice"})
        self.assertTrue(move.llm_ocr_enabled)

        self.assistant.active = False
        move.invalidate_recordset(["llm_ocr_enabled"])
        self.assertFalse(move.llm_ocr_enabled)

        self.assistant.active = True
        move.invalidate_recordset(["llm_ocr_enabled"])
        self.assertTrue(move.llm_ocr_enabled)

    def test_menu_visible_to_finance_user_when_enabled(self):
        user = self._create_internal_user("ocr_test_menu_enabled", finance=True)
        self.assertIn(self.menu.id, self._visible_menu_ids(user))

    def test_menu_hidden_when_assistant_archived(self):
        user = self._create_internal_user("ocr_test_menu_archived", finance=True)
        self.assistant.active = False
        self.assertNotIn(self.menu.id, self._visible_menu_ids(user))

    def test_menu_returns_when_assistant_unarchived(self):
        """Proves nothing stale is kept: the menu follows the assistant's
        state on every call, in both directions."""
        user = self._create_internal_user("ocr_test_menu_toggle", finance=True)
        self.assistant.active = False
        self.assertNotIn(self.menu.id, self._visible_menu_ids(user))

        self.assistant.active = True
        self.assertIn(self.menu.id, self._visible_menu_ids(user))

    def test_menu_hidden_when_assistant_missing(self):
        user = self._create_internal_user("ocr_test_menu_missing", finance=True)
        self.assistant.code = "not_invoice_extraction_anymore"
        self.assertNotIn(self.menu.id, self._visible_menu_ids(user))

    def test_menu_follows_a_replacement_assistant(self):
        """A different assistant taking over the invoice_extraction code
        (llm.assistant.code is unique, so the original has to give it up
        first) brings the menu back with no reactivation step."""
        user = self._create_internal_user("ocr_test_menu_replaced", finance=True)
        self.assistant.code = "invoice_extraction_old"
        self.assertNotIn(self.menu.id, self._visible_menu_ids(user))

        self.env["llm.assistant"].create(
            {
                "name": "Replacement Assistant",
                "code": "invoice_extraction",
                "prompt_id": self.assistant.prompt_id.id,
            }
        )
        self.assertIn(self.menu.id, self._visible_menu_ids(user))

    def test_menu_never_visible_without_invoicing_access(self):
        user = self._create_internal_user("ocr_test_menu_plain")
        self.assertNotIn(self.menu.id, self._visible_menu_ids(user))

    def test_archiving_unrelated_assistant_keeps_menu_visible(self):
        """Archiving any other assistant must not hide the menu."""
        prompt = self.env["llm.prompt"].create(
            {"name": "Unrelated Prompt", "template": "Hello"}
        )
        other = self.env["llm.assistant"].create(
            {
                "name": "Unrelated Assistant",
                "code": "unrelated_code",
                "prompt_id": prompt.id,
            }
        )
        user = self._create_internal_user("ocr_test_unrelated", finance=True)
        self.assertIn(self.menu.id, self._visible_menu_ids(user))

        other.active = False
        self.assertIn(self.menu.id, self._visible_menu_ids(user))

    def test_upload_falls_back_to_core_decoders_when_disabled(self):
        self.assistant.active = False
        attachment = self._create_fake_attachment()
        wizard_count_before = self.env["account.invoice.import"].search_count([])

        action = (
            self.env["account.journal"]
            .with_context(default_move_type="in_invoice")
            .create_document_from_attachment(attachment.ids)
        )

        self.assertEqual(
            self.env["account.invoice.import"].search_count([]),
            wizard_count_before,
            "No review wizard should be created while AI import is disabled.",
        )
        self.assertEqual(action["res_model"], "account.move")
        self.assertIn("notifications", action.get("context") or {})
        self.assertIn(attachment.name, action["context"]["notifications"])

    def test_upload_opens_wizard_when_enabled(self):
        """Regression: the enabled path (from Ticket 0141016) must be
        untouched by this ticket's changes."""
        attachment = self._create_fake_attachment()

        action = (
            self.env["account.journal"]
            .with_context(default_move_type="in_invoice")
            .create_document_from_attachment(attachment.ids)
        )

        self.assertEqual(action["res_model"], "account.invoice.import")
        self.assertNotIn("notifications", action.get("context") or {})

    def test_upload_unaffected_for_non_vendor_bills_when_disabled(self):
        """Disabling AI import must not touch the customer-invoice/other
        move-type branch, which never used it in the first place."""
        self.assistant.active = False
        attachment = self._create_fake_attachment()

        action = (
            self.env["account.journal"]
            .with_context(default_move_type="out_invoice")
            .create_document_from_attachment(attachment.ids)
        )

        self.assertEqual(action["res_model"], "account.move")
        self.assertNotIn("notifications", action.get("context") or {})

    def test_wizard_blocked_when_disabled(self):
        """Reaching the wizard directly (the "Import Vendor Bills" menu
        action, or a stale session where it's still visible) must be
        blocked at default_get(), before the form even opens - not just
        once the user has already picked a file and clicked Import."""
        self.assistant.active = False
        with self.assertRaises(UserError):
            self.env["account.invoice.import"].create({})

    def test_wizard_not_blocked_when_enabled(self):
        wizard = self.env["account.invoice.import"].create({})
        self.assertTrue(wizard)

    def _visible_menu_ids(self, user):
        return self.env["ir.ui.menu"].with_user(user)._visible_menu_ids()

    def _create_internal_user(self, login, finance=False):
        groups = [(4, self.env.ref("base.group_user").id)]
        if finance:
            groups.append((4, self.env.ref("account.group_account_invoice").id))
        return self.env["res.users"].create(
            {
                "name": login,
                "login": login,
                "email": f"{login}@example.test",
                "groups_id": groups,
            }
        )

    def _create_fake_attachment(self):
        return self.env["ir.attachment"].create(
            {"name": "invoice.pdf", "datas": b"ZmFrZQ=="}
        )
