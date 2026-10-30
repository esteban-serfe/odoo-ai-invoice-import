# llm_access_groups
Odoo 16 module that restricts who can use the `odoo-llm` features. It leaves those modules untouched: records are patched by external ID.

## What is this for?
- Restricts the LLM Configuration, Prompts and Training menus to *LLM Manager*. The upstream modules leave them open to every internal user.
- Adds the *User: LLM Chatter* group, required to use the AI chat (chatter "AI" button, Chat menu, `llm.thread`). The `llm.thread` ACL, its personal-threads record rule and the Chat menu move from *Internal User* to this group.
- Hides the chatter "AI" button from users outside that group.

## Requirements / Dependencies
- Odoo 16 (Community)
- Odoo modules: `serfe_llm_assistant`, `serfe_llm_thread`, `serfe_llm_training`

## Installation
Add the addon to your addons path and install it (Apps, or `-i llm_access_groups`).

## Configuration
To let a user chat with the LLM, add them to *User: LLM Chatter* (or *LLM Manager*).

## Security / Access
- **User: LLM Chatter** (`llm_access_groups.group_llm_chatter_user`) implies *Internal User*.
- **LLM Manager** (`serfe_llm.group_llm_manager`) implies *User: LLM Chatter* and keeps access to the Configuration, Prompts and Training menus.
- Hiding the chatter button is cosmetic; the real restriction is the `llm.thread` ACL.

## Multi-company behavior
Groups are global, not per company.

## Licence
LGPL-3
