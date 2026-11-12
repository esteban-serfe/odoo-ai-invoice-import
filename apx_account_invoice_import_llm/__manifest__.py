{
    "name": "Invoice Import LLM",
    "summary": "Vendor bill data extraction with OCR and an LLM",
    "description": """
Reads a supplier invoice (PDF or image) with an OCR step and one LLM call, and
creates a draft vendor bill through OCA's account_invoice_import: a "Process
with AI" button and a fallback for the import wizard.

The OCR step inherited from Apexive looks for a Mistral provider; in this
repository serfe_invoice_ocr replaces it with LiteLLM, so install it together
with this module.

Data notice: the documents are sent to the AI provider that you configure.
The module does not send data to Serfe or to any fixed service.
    """,
    "category": "Accounting/AI",
    "version": "16.0.1.0.3",
    "depends": [
        "account_invoice_import",  # OCA invoice import wizard (fallback_parse_pdf_invoice)
        "apx_llm_assistant",  # Includes apx_llm, apx_llm_thread, apx_llm_tool
        # llm_mistral replaced by llm_litellm: OCR goes through the LiteLLM
        # provider (see serfe_invoice_ocr). llm_mistral only pulled in llm_openai
        # and the openai library, which were never used.
        "apx_llm_litellm",
    ],
    "author": "Apexive Solutions LLC, Serfe",
    "website": "https://github.com/apexive/odoo-llm",
    "data": [
        "data/llm_prompt_invoice_data.xml",
        "data/llm_assistant_data.xml",
        "views/account_move_views.xml",
    ],
    "license": "AGPL-3",
    "installable": True,
    "application": False,
    "auto_install": False,
    "pre_init_hook": "pre_init_hook",
    "images": [
        "static/description/banner.jpeg",
    ],
}
