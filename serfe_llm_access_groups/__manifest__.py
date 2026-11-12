{
    "name": "Serfe LLM Access Groups",
    "version": "16.0.1.0.0",
    "summary": "Restrict the LLM menus to LLM Manager and the AI chat to a "
    "dedicated group",
    "author": "Serfe",
    "license": "LGPL-3",
    "category": "Technical",
    "depends": [
        "apx_llm_assistant",
        "apx_llm_thread",
        "apx_llm_training",
    ],
    "data": [
        "security/llm_menu_security.xml",
        "security/llm_chatter_security.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "serfe_llm_access_groups/static/src/models/chatter.js",
            "serfe_llm_access_groups/static/src/components/llm_chatter_topbar.xml",
        ],
    },
    "installable": True,
    "application": False,
}
