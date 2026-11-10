# llm_invoice_ocr

[Español](README.md)

Odoo 16 module that tunes the AI invoice import for Argentine vendor bills (AFIP). It is focused on Argentina and other countries are not covered: contact Serfe if you need them. It reads the PDF or image of a supplier invoice with an LLM and creates a draft vendor bill for review.

## What is this for?
It extends `serfe_account_invoice_import_llm` so it works through the LiteLLM provider of `llm_litellm_responses` and understands AFIP documents.

- **LiteLLM instead of the default OCR provider:** the invoice is transcribed and analysed through the model configured on the *Invoice Extraction* assistant, so OCR and extraction use the same provider. Only LiteLLM providers are supported.
- **Argentine prompt:** the assistant's prompt is replaced with one tuned for AFIP invoices. It first decides whether the document is really an invoice, reads the vendor's CUIT, reads dates day-first, extracts the point-of-sale and number as printed, the voucher letter (A/B/C), and document-level charges. It asks for the printed VAT rate with its evidence instead of a remembered one.
- **Company VAT rates in the prompt:** the purchase VAT rates configured for the company are added to the prompt, so unusual rates (such as 27% on telecom, gas or electricity) are not replaced by a common one. Only for Argentine companies with `l10n_ar`.
- **Document type and number:** the detected letter selects the Latam document type and number. For letters B and C every line gets *VAT Not Applicable*, as `l10n_ar` requires.
- **VAT percentage correction:** the rate implied by the extracted subtotal and total replaces the per-line rate when they disagree. It applies only when all lines agree on a single VAT tax.
- **Perceptions as taxes:** *Percepción IIBB / IVA* are applied as the matching AFIP tribute tax on the existing lines.
- **Best effort:** any step that cannot be resolved leaves the draft as extracted for manual review. It never blocks the import.
- **Upload button:** on vendor bills and refunds, *Upload* opens the review wizard. Other lists use Odoo's standard document decoders.
- **Switching it off:** archiving the *Invoice Extraction* assistant disables AI import. The *Process with AI* button and the *Import Vendor Bills* menu disappear, the wizard refuses to open, and *Upload* creates the bill with the standard decoders and shows a notice.
- **Messages:** the *Process with AI* guard errors are translatable.

## Requirements / Dependencies
- Odoo 16 (Community)
- Odoo modules: `llm_litellm_responses`, `serfe_account_invoice_import_llm`, `serfe_llm_litellm`
- Optional: `l10n_ar` for the Argentine behavior
- A LiteLLM proxy and an AI provider account, both provided by you (see `llm_litellm_responses`). LiteLLM works with the API of each provider: refer to the LiteLLM and provider documentation to configure them.

## Installation
1. Make the addon and its dependencies available in your addons path.
2. Install `llm_litellm_responses`. If `LITELLM_API_BASE` and `LITELLM_API_KEY` are set in the environment, it creates the *LiteLLM* provider; otherwise create it from the UI (*LLM → Configuration → Providers*) with your proxy URL and API key.
3. Fetch the models of that provider (*Fetch Models* in the provider form).
4. Install the module (Apps, or `-i llm_invoice_ocr`).

If a model already exists on the provider, the install sets it on the *Invoice Extraction* assistant. If not, it only logs a warning: assign a model to the assistant under *LLM → Configuration → Assistants*, or upgrade the module again once a model is fetched.

## Configuration
No environment variables or system parameters of its own. Configuration is the model of the *Invoice Extraction* assistant, and the provider settings of `llm_litellm_responses`.

## Security / Access
- No groups, ACLs or record rules are added; standard accounting permissions apply.
- The invoice document is sent to the AI provider you configured through your LiteLLM proxy. Serfe does not receive it.
- AI output is a suggestion: totals, taxes and the vendor must be checked before posting.

## Multi-company behavior
VAT rates and the *VAT Not Applicable* tax are read from the company of the bill, so each company uses its own configured taxes. The prompt names the importing company and its CUIT so the model does not confuse it with the vendor. The assistant and provider are shared as configured.

## Licence
AGPL-3 (it depends on `serfe_account_invoice_import_llm`, which is AGPL-3).
