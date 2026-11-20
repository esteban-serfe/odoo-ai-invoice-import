Argentina Invoice OCR
=====================

Install the addon and its OCA dependencies in Odoo 16 Community. Configure
the Argentine chart of accounts, AFIP responsibility, purchase journal and
taxes before importing bills. This Python addon does not run on Odoo Online.

Configure a LiteLLM or compatible endpoint under LLM → Configuration →
Providers. Use HTTPS for external services. Fetch models and assign a model
that supports document inputs through streaming ``/responses`` and structured
extraction through ``/chat/completions`` to the Invoice Extraction assistant.

External processing is off by default. In the company's Invoice AI tab, an
administrator must review and authorize the transfer. The configured endpoint
receives the entire invoice, its transcription, extraction prompts, and the
company name, CUIT, currency and purchase VAT rates. The endpoint may forward
the data to downstream providers and charge for processing. Review the
applicable privacy and retention terms first.

Upload a PDF, PNG or JPEG (at most 20 MiB) from Vendor Bills, or select
Process with AI on an existing draft with an attachment. Review the vendor,
document type and number, dates, lines, VAT, perceptions and total before
posting. The addon does not post automatically or verify the invoice with AFIP.

Turn off the company option to stop future AI invoice requests for that
company, or archive the shared assistant to disable AI invoice processing
for all companies. Vendor bill uploads then use Odoo's standard decoders.
