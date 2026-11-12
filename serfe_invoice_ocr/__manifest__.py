{
    "name": "Serfe Invoice OCR",
    "version": "16.0.1.0.0",
    "summary": "AI vendor bill import tuned for Argentine (AFIP) invoices",
    "description": """
Reads the PDF or image of a supplier invoice with an LLM and creates a draft
vendor bill for review: vendor CUIT, voucher letter and Latam document type,
point of sale and number, day-first dates, printed VAT rate, perceptions and
document-level charges. Focused on Argentina.

Data notice: the documents and prompts are sent to the AI provider that you
configure through your own LiteLLM proxy. The module does not send data to
Serfe or to any fixed service.
    """,
    "author": "Serfe",
    "license": "AGPL-3",
    "category": "Accounting",
    "depends": [
        "serfe_llm_litellm_responses",
        "apx_account_invoice_import_llm",
        "apx_llm_litellm",
    ],
    "data": [
        "data/invoice_extraction_assistant_data.xml",
        "views/account_move_views.xml",
    ],
    "installable": True,
    "application": False,
    "post_init_hook": "post_init_hook",
}
