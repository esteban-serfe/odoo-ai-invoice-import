"""Access to the AI chat (llm.thread) is limited to the "User: LLM Chatter"
group; a plain internal user must be refused by the ACL itself, not just by a
hidden menu.
"""

from odoo.exceptions import AccessError
from odoo.tests.common import TransactionCase


class TestLLMChatterGroup(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = cls.env.ref("llm_access_groups.group_llm_chatter_user")
        cls.internal = cls.env["res.users"].create(
            {
                "name": "Plain Internal",
                "login": "plain_internal_llm",
                "groups_id": [(6, 0, [cls.env.ref("base.group_user").id])],
            }
        )
        cls.chatter = cls.env["res.users"].create(
            {
                "name": "LLM Chatter",
                "login": "llm_chatter_user",
                "groups_id": [(6, 0, [cls.group.id])],
            }
        )
        cls.manager = cls.env["res.users"].create(
            {
                "name": "LLM Manager",
                "login": "llm_manager_user",
                "groups_id": [(6, 0, [cls.env.ref("llm.group_llm_manager").id])],
            }
        )

    def test_plain_internal_user_cannot_use_llm_thread(self):
        with self.assertRaises(AccessError):
            self.env["llm.thread"].with_user(self.internal).check_access_rights("read")

    def test_chatter_user_can_use_llm_thread(self):
        self.env["llm.thread"].with_user(self.chatter).check_access_rights("read")
        self.env["llm.thread"].with_user(self.chatter).check_access_rights("create")

    def test_manager_implies_chatter_group(self):
        self.assertIn(self.group, self.manager.groups_id)

    def test_chat_menu_is_restricted_to_group(self):
        menu = self.env.ref("serfe_llm_thread.menu_llm_chat")
        self.assertEqual(menu.groups_id, self.group)

    def test_session_flag_follows_group(self):
        flag = "llm_access_groups.group_llm_chatter_user"
        self.assertFalse(self.internal.has_group(flag))
        self.assertTrue(self.chatter.has_group(flag))
