{
    "name": "LLM Invoice OCR (Argentina)",
    "version": "16.0.1.0.0",
    "summary": (
        "Argentine-tuned LLM/OCR invoice extraction, built as extensions on "
        "top of the unmodified serfe_account_invoice_import_llm module"
    ),
    "author": "Serfe",
    "license": "AGPL-3",
    "category": "Accounting",
    "depends": [
        "llm_litellm_responses",
        "serfe_account_invoice_import_llm",
        "serfe_llm_litellm",
    ],
    "data": [
        "data/invoice_extraction_assistant_data.xml",
        "views/account_move_views.xml",
    ],
    "installable": True,
    "application": False,
    "post_init_hook": "post_init_hook",
}
