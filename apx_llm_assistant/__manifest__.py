{
    "name": "LLM Assistant",
    "summary": """
        LLM/AI Assistant module with prompt templates for Odoo
    """,
    "description": """
LLM Assistant with Prompt Templates for Odoo
==================
Configure AI assistants with specific roles, goals, and tools to enhance your AI interactions.
Includes comprehensive prompt template management for reusable LLM interactions.

Key Features:
- Create and configure AI assistants with specific roles and goals
- Assign preferred tools to each assistant
- Automatically generate system prompts based on assistant configuration
- Attach assistants to chat threads for consistent behavior
- Full integration with the LLM chat system
- Create reusable prompt templates in text, YAML, or JSON format
- Dynamic arguments within prompts
- Multi-step prompt workflows through structured formats
- Prompt discovery and retrieval
- Categories and tags for organization
- Enhanced prompt testing with context simulation
- Related record integration for prompt testing

Use cases include creating specialized assistants for customer support, data analysis, training assistance, and more.
    """,
    "category": "Productivity, Discuss",
    "version": "16.0.1.5.3",
    "depends": [
        "base",
        "mail",
        "web",
        "apx_llm",
        "apx_llm_thread",
        "apx_llm_tool",
        "apx_web_json_editor",
    ],
    "external_dependencies": {
        "python": ["jinja2", "jsonschema", "pyyaml"],
    },
    "author": "Apexive Solutions LLC, Serfe",
    "website": "https://github.com/apexive/odoo-llm",
    "data": [
        "security/ir.model.access.csv",
        "data/llm_prompt_tag_data.xml",
        "data/llm_prompt_category_data.xml",
        "data/llm_prompt_export_data.xml",
        "data/llm_prompt_data.xml",
        "data/llm_assistant_data.xml",
        "views/llm_prompt_views.xml",
        "views/llm_prompt_tag_views.xml",
        "views/llm_prompt_category_views.xml",
        "views/llm_assistant_views.xml",
        "views/llm_thread_views.xml",
        "views/llm_menu_views.xml",
        "wizards/llm_prompt_test_views.xml",
    ],
    "images": [
        "static/description/banner.jpeg",
    ],
    "assets": {
        "web.assets_backend": [
            "apx_llm_assistant/static/src/models/main.js",
            # Models
            "apx_llm_assistant/static/src/models/llm_assistant.js",
            "apx_llm_assistant/static/src/models/llm_prompt.js",
            "apx_llm_assistant/static/src/models/llm_chat.js",
            "apx_llm_assistant/static/src/models/thread.js",
            "apx_llm_assistant/static/src/models/llm_chat_thread_header_view.js",
            # Components
            "apx_llm_assistant/static/src/components/llm_chat_thread_header/llm_chat_thread_header.js",
            "apx_llm_assistant/static/src/components/llm_chat_thread_header/llm_chat_thread_header.xml",
        ],
    },
    "license": "LGPL-3",
    "installable": True,
    "application": False,
    "auto_install": False,
}
