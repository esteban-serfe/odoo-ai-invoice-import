{
    "name": "Argentina Invoice OCR",
    "version": "16.0.1.1.0",
    "summary": "AI vendor bill import tuned for Argentine (AFIP) invoices",
    "description": """
Reads the PDF or image of a supplier invoice with an LLM and creates a draft
vendor bill for review: vendor CUIT, voucher letter and Latam document type,
point of sale and number, day-first dates, printed VAT rate, perceptions and
document-level charges. Focused on Argentina.

External AI is off until an administrator opts in for the company. A supported
LiteLLM or compatible endpoint receives the full invoice document and then its
transcription, prompts, company name, CUIT, currency and purchase VAT rates. That endpoint
may forward data to downstream providers. No fixed destination or Serfe service
is built in. AI processing may incur provider fees.
    """,
    "author": "Serfe",
    "website": "https://www.serfe.com/",
    "license": "AGPL-3",
    "category": "Accounting",
    "depends": [
        "apx_account_invoice_import_llm",
        "apx_llm_litellm",
        "l10n_ar",
    ],
    "data": [
        "data/llm_provider_data.xml",
        "data/invoice_extraction_assistant_data.xml",
        "views/account_move_views.xml",
        "views/res_company_views.xml",
    ],
    "installable": True,
    "application": True,
    "images": [
        "static/description/cover.png",
        "static/description/draft_bill_screenshot.png",
    ],
    "post_init_hook": "post_init_hook",
}
