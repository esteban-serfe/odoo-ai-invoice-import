# odoo-ai-addons

Odoo 16 addons for LLM features: a subset of [apexive/odoo-llm](https://github.com/apexive/odoo-llm)
plus extensions for LiteLLM, access control and Argentine invoice OCR.

Branch `16.0`. Modules live at the repository root; add the repository to the `addons_path`.

## Modules

| Module | License | Origin | Description |
|---|---|---|---|
| `llm` | LGPL-3 | apexive/odoo-llm | Providers, models, publishers |
| `llm_thread` | LGPL-3 | apexive/odoo-llm | Chat threads and chatter integration |
| `llm_tool` | LGPL-3 | apexive/odoo-llm | Tools callable by the model |
| `llm_assistant` | LGPL-3 | apexive/odoo-llm | Assistants and prompts |
| `llm_litellm` | LGPL-3 | apexive/odoo-llm | LiteLLM provider |
| `llm_training` | LGPL-3 | apexive/odoo-llm | Training datasets and jobs |
| `web_json_editor` | LGPL-3 | apexive/odoo-llm | JSON editor field widget |
| `account_invoice_import_llm` | AGPL-3 | apexive/odoo-llm | Vendor bill import with LLM and OCR |
| `llm_litellm_responses` | LGPL-3 | this repo | Responses API, OCR retries, provider auto-provisioning |
| `llm_access_groups` | LGPL-3 | this repo | *LLM Chatter* group, manager-only LLM menus |
| `llm_invoice_ocr` | AGPL-3 | this repo | Argentine (AFIP) tuning for the invoice import |

See [UPSTREAM.md](UPSTREAM.md) for the base commit and the local changes to the vendored modules.
Each module has its own README with configuration details.

## Dependencies

* Odoo 16 Community.
* OCA repositories listed in `oca_dependencies.txt` (`account_invoice_import` comes from OCA/edi).
* Python packages in `requirements.txt`: `pip install -r requirements.txt`.
* A [LiteLLM](https://github.com/BerriAI/litellm) proxy for `llm_litellm_responses` and `llm_invoice_ocr`.

## LiteLLM configuration

`llm_litellm_responses` creates the *LiteLLM* provider on install from the environment of the Odoo process:

```
LITELLM_API_BASE=https://your-litellm-proxy.example
LITELLM_API_KEY=sk-...
```

There is no default URL. If either variable is missing the install continues without a provider, which you can then create by hand.

## Tests and lint

```
scripts/run-tests.sh                      # all modules
scripts/run-tests.sh llm_invoice_ocr      # some modules
pre-commit run --all-files                # black, isort, flake8, pylint-odoo
```

Needs Docker. The script clones the OCA repos of `oca_dependencies.txt` into `.oca/`, builds an Odoo 16 image
(`scripts/Dockerfile`, or set `ODOO_IMAGE`), and runs the tests on a clean throwaway database, on an internal
Docker network (no internet) and without `LITELLM_API_BASE` / `LITELLM_API_KEY`.
Lint covers only the modules written in this repo; the vendored ones are excluded to keep them diffable against upstream.

## License

Mixed, per module. See [LICENSE](LICENSE).
