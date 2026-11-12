# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Vendored from apexive/odoo-llm at `a6a229d`, renamed with the `apx_` prefix (for Apexive) so they do not clash with Apexive's modules in the Odoo Apps store: `apx_llm`, `apx_llm_thread`, `apx_llm_tool`, `apx_llm_assistant`, `apx_llm_litellm`, `apx_llm_training`, `apx_web_json_editor`, `apx_account_invoice_import_llm`.
- `serfe_llm_litellm_responses`: Responses API, orphaned tool message cleanup, OCR with retries, `model_info`, provider auto-provisioning from `LITELLM_API_BASE` and `LITELLM_API_KEY`.
- `serfe_llm_access_groups`: *LLM Chatter* group, LLM menus limited to *LLM Manager*, chatter "AI" button hidden from other users.
- `serfe_invoice_ocr`: Argentine (AFIP) extension of `apx_account_invoice_import_llm`.
- Icon and description for the modules published in the Odoo Apps store.
- Self-contained test runner (`scripts/run-tests.sh`) and lint configuration.

### Changed

- `apx_llm_litellm`: tool calling and extra chat completion parameters.
- `apx_account_invoice_import_llm`: depends on `apx_llm_litellm` instead of `llm_mistral`.

### Fixed

- Manifests follow the Odoo Apps store rules: names of at most 25 characters, `16.0.x.y.z` version for `apx_web_json_editor`, and `jsonschema` in the external dependencies of `apx_llm_assistant`.
- Test runner runs the container as the `odoo` user.
- `apx_llm_thread`: bus error in the notification handler patch.
- `apx_web_json_editor`: `json_inline` widget alias.
- `apx_llm_assistant`: invalid `attrs` on the ace widget of the prompt views.
