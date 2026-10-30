# odoo-ai-addons

[Español](README.es.md)

Odoo 16 addons to chat with LLMs, restrict who can use them, and import vendor bills with AI, through a LiteLLM proxy.

## Key Features

* Chat with an LLM from any record's chatter, with assistants, prompts and tools.
* LiteLLM provider with the Responses API, tool calling and OCR with retries.
* Access control: a dedicated *LLM Chatter* group, and LLM configuration menus limited to *LLM Manager*.
* Vendor bill import from PDF or image with an LLM, tuned for Argentine (AFIP) invoices.

## Scope

The vendor bill import is focused on Argentina (CUIT, voucher letters, AFIP taxes, `l10n_ar`). Other countries, such as Uruguay, are not covered: [contact us](https://www.serfe.com/en/) if you need them.

## Requirements

* Odoo 16 Community.
* `account_invoice_import` from [OCA/edi](https://github.com/OCA/edi), plus the other repositories in `oca_dependencies.txt`.
* An AI provider account (OpenAI, Anthropic, Mistral, etc.) and a [LiteLLM](https://github.com/BerriAI/litellm) proxy in front of it, both provided and operated by you. Serfe does not supply the AI service. LiteLLM works with the API of each provider: see the [LiteLLM documentation](https://docs.litellm.ai/) and your provider's documentation to set it up.
* The URL and API key of your LiteLLM proxy. You enter them in the *LiteLLM* provider from the Odoo UI (see Configuration). Optionally, you can provide them as environment variables of the Odoo process so the provider is created on install:

| Variable | Description |
|---|---|
| `LITELLM_API_BASE` | URL of your LiteLLM proxy. Optional, there is no default. |
| `LITELLM_API_KEY` | API key of your LiteLLM proxy. Optional. |

## Modules

| Module | Description | Origin |
|---|---|---|
| `serfe_llm` | Providers, models, publishers | fork of [apexive/odoo-llm](https://github.com/apexive/odoo-llm) `llm` |
| `serfe_llm_thread` | Chat threads and chatter integration | fork of apexive/odoo-llm `llm_thread` |
| `serfe_llm_tool` | Tools callable by the model | apexive/odoo-llm |
| `serfe_llm_assistant` | Assistants and prompts | fork of `llm_assistant` |
| `serfe_llm_litellm` | LiteLLM provider | fork of `llm_litellm` |
| `serfe_llm_training` | Training datasets and jobs | apexive/odoo-llm |
| `serfe_web_json_editor` | JSON editor field widget | fork of `web_json_editor` |
| `serfe_account_invoice_import_llm` | Vendor bill import with LLM and OCR | fork of `account_invoice_import_llm` |
| `llm_litellm_responses` | Responses API, OCR retries, provider auto-provisioning | this repo |
| `llm_access_groups` | *LLM Chatter* group, manager-only LLM menus | this repo |
| `llm_invoice_ocr` | Argentine (AFIP) tuning for the invoice import | this repo |

The vendored modules keep their original authorship. All eight carry the `serfe_` prefix so they do not clash with Apexive's modules of the same name in the Odoo Apps store; do not install both. See [UPSTREAM.md](UPSTREAM.md) for the base commit and the local changes.
Each module has its own README.

## Installation Guide

1. Clone this repository (branch `16.0`) and the repositories listed in `oca_dependencies.txt`.
2. Add them to the `addons_path` of Odoo.
3. Install the Python dependencies: `pip install -r requirements.txt`.
4. Update the apps list and install the modules you need.
5. Optional: if `LITELLM_API_BASE` and `LITELLM_API_KEY` are set in the environment of the Odoo process, `llm_litellm_responses` creates the *LiteLLM* provider on install. Without them it installs normally and you configure the provider from the UI.

## Configuration Instructions

1. Open *LLM → Configuration → Providers*, create or open the *LiteLLM* provider (service *LiteLLM*), and fill in the *API Base* (your proxy URL) and *API Key*. Skip this if the provider was already created from the environment variables. Then use *Fetch Models* to import the models of the proxy.
2. Assign a model to the *Invoice Extraction* assistant (*LLM → Configuration → Assistants*) to enable `llm_invoice_ocr`.
3. Add the users who may chat with the LLM to the *User: LLM Chatter* group (`llm_access_groups`). *LLM Manager* includes it.

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
