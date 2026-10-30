# AI vendor bill import for Odoo (Argentina)

[Español](README.es.md)

Upload a supplier invoice (PDF or image) to Odoo 16 and get a draft vendor bill with the Argentine (AFIP) data already filled in, ready for review. It uses a language model (ChatGPT or another) that you choose, through the API of your own provider.

## The problem

Loading vendor bills by hand is repetitive: copying the vendor, CUIT, voucher type, point of sale and number, dates, VAT and perceptions, line by line. It takes operating time and invites typing mistakes.

## What it does

* **Reads the invoice** from a PDF or an image and creates a **draft vendor bill**. It never posts it.
* **Understands Argentine invoices:** the vendor's CUIT, the voucher letter (A, B or C) and the matching Latam document type, point of sale and number as printed, day-first dates, the printed VAT rate, and perceptions (IIBB and VAT) applied as the matching AFIP tax.
* **Keeps unusual VAT rates**, such as 27% on telecom, gas or electricity, because your company's purchase VAT rates are part of what the model is given.
* **Is built to be reviewed:** a step that cannot be resolved leaves the draft as extracted instead of blocking the import.
* **Can be switched off:** archiving the *Invoice Extraction* assistant disables the AI import, and *Upload* goes back to Odoo's standard decoders.

## How it works

1. On a vendor bill or refund list, press *Upload* and choose the PDF or image (or use *Process with AI* on an existing draft bill).
2. The document is read and the data is extracted with the model you configured.
3. A review wizard opens with the result. You check totals, taxes and the vendor, fix what is needed and post.

It is built on [`account_invoice_import`](https://github.com/OCA/edi) from OCA, so vendor, product and tax matching are the standard ones.

## Limitations

* **Argentina only.** The extraction is tuned for AFIP invoices (CUIT, voucher letters, AFIP taxes, `l10n_ar`). Other countries, such as Uruguay, are not covered: [contact us](https://www.serfe.com/en/) if you need them.
* **Odoo 16 Community only.** Other versions have not been reviewed.
* **The model can be wrong.** The result is a suggestion: check totals, taxes and the vendor before posting. Poor scans or unusual layouts may give incomplete drafts.
* **Providers are reached through LiteLLM**, a proxy that you run in front of your AI provider.
* **The API key of the provider is stored in the Odoo provider record, and every internal user can read it.** Use a key with a limited budget, or restrict who has internal user access.

## Costs and data

* **No license fee.** The modules are free and open source.
* **Your costs:** the usage of your AI provider (it depends on the provider, the model and the size of the documents) and the hosting of your LiteLLM proxy. Serfe does not provide the AI service.
* **Your data:** each invoice is sent to the AI provider that you configure through your own LiteLLM proxy. Serfe does not receive it. Check your provider's data policy before processing documents.

## Requirements

* Odoo 16 Community, with `l10n_ar` for the Argentine behavior.
* `account_invoice_import` from [OCA/edi](https://github.com/OCA/edi), plus the other repositories in `oca_dependencies.txt`.
* An AI provider account (OpenAI, Anthropic, Mistral, etc.) and a [LiteLLM](https://github.com/BerriAI/litellm) proxy in front of it, both provided and operated by you. LiteLLM works with the API of each provider: see the [LiteLLM documentation](https://docs.litellm.ai/) and your provider's documentation to set it up.

## Installation

1. Clone this repository (branch `16.0`) and the repositories listed in `oca_dependencies.txt`.
2. Add them to the `addons_path` of Odoo.
3. Install the Python dependencies: `pip install -r requirements.txt`.
4. Update the apps list and install `llm_invoice_ocr`; its dependencies are installed with it.

## Configuration

1. Open *LLM → Configuration → Providers*, create or open the *LiteLLM* provider (service *LiteLLM*), and fill in the *API Base* (your proxy URL) and *API Key*. Then use *Fetch Models* to import the models of the proxy.
2. Assign a model to the *Invoice Extraction* assistant (*LLM → Configuration → Assistants*).

Optionally, set `LITELLM_API_BASE` and `LITELLM_API_KEY` in the environment of the Odoo process before installing, and `llm_litellm_responses` creates the *LiteLLM* provider for you. There is no default value for either.

## Modules

The invoice import uses these modules of the repository:

| Module | Description | Origin |
|---|---|---|
| `llm_invoice_ocr` | Argentine (AFIP) tuning for the invoice import | this repo |
| `serfe_account_invoice_import_llm` | Vendor bill import with LLM and OCR | fork of [apexive/odoo-llm](https://github.com/apexive/odoo-llm) `account_invoice_import_llm` |
| `llm_litellm_responses` | Responses API, OCR retries, provider auto-provisioning | this repo |
| `serfe_llm_litellm` | LiteLLM provider | fork of `llm_litellm` |

The rest is the base they run on, and can also be used to chat with a model from any record's chatter:

| Module | Description | Origin |
|---|---|---|
| `serfe_llm` | Providers, models, publishers | fork of `llm` |
| `serfe_llm_assistant` | Assistants and prompts | fork of `llm_assistant` |
| `serfe_llm_thread` | Chat threads and chatter integration | fork of `llm_thread` |
| `serfe_llm_tool` | Tools callable by the model | renamed copy of `llm_tool` |
| `serfe_llm_training` | Training datasets and jobs | renamed copy of `llm_training` |
| `serfe_web_json_editor` | JSON editor field widget | fork of `web_json_editor` |
| `llm_access_groups` | *LLM Chatter* group, manager-only LLM menus | this repo |

The vendored modules keep their original authorship. All eight carry the `serfe_` prefix so they do not clash with Apexive's modules of the same name in the Odoo Apps store; do not install both. See [UPSTREAM.md](UPSTREAM.md) for the base commit and the local changes.
Each module has its own README.

## Publishing in the Odoo Apps store

The store reads a git repository whose branch is named after the Odoo version (`16.0`) and resolves dependencies on its own. Every module in this repository carries the `serfe_` prefix, or is ours, and the OCA modules it depends on are published in the store, so the repository can be registered as is.

## Contributing

1. Fork the repository and create a branch from `16.0`.
2. Make your change, using [conventional commits](https://www.conventionalcommits.org/).
3. Run the tests and the lint (Docker required):

   ```
   scripts/run-tests.sh                      # all modules
   scripts/run-tests.sh llm_invoice_ocr      # some modules
   pre-commit run --all-files                # black, isort, flake8, pylint-odoo
   ```

   The script clones the OCA repositories into `.oca/`, builds an Odoo 16 image (`scripts/Dockerfile`, or set `ODOO_IMAGE`)
   and runs the tests on a clean database, on an internal Docker network and without `LITELLM_*` set.
   Lint covers only the modules written in this repository; the vendored ones are excluded to stay diffable against upstream.
4. Open a pull request.

## License

Mixed, per module. See [LICENSE](LICENSE).

## About Us

Maintained by [Serfe](https://www.serfe.com/en/). Questions about setup or adapting the modules to your case are welcome: contact us.
