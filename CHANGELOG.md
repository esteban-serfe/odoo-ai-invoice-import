# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Vendored from apexive/odoo-llm at `a6a229d`: `llm`, `llm_tool`, `llm_training` as they are, and `llm_thread`, `llm_assistant`, `llm_litellm`, `web_json_editor`, `account_invoice_import_llm` renamed with the `serfe_` prefix (`serfe_llm_thread`, ...) so they do not clash with Apexive's modules of the same name in the Odoo Apps store.
- `llm_litellm_responses`: Responses API, orphaned tool message cleanup, OCR with retries, `model_info`, provider auto-provisioning from `LITELLM_API_BASE` and `LITELLM_API_KEY`.
- `llm_access_groups`: *LLM Chatter* group, LLM menus limited to *LLM Manager*, chatter "AI" button hidden from other users.
- `llm_invoice_ocr`: Argentine (AFIP) extension of `serfe_account_invoice_import_llm`.
- `scripts/export-store.sh`: exports the modules to publish in the Odoo Apps store, with an icon and a description for each.
- Self-contained test runner (`scripts/run-tests.sh`) and lint configuration.

### Changed

- `serfe_llm_litellm`: tool calling and extra chat completion parameters.
- `serfe_account_invoice_import_llm`: depends on `serfe_llm_litellm` instead of `llm_mistral`.

### Fixed

- Manifests follow the Odoo Apps store rules: names of at most 25 characters, `16.0.x.y.z` version for `serfe_web_json_editor`, and `jsonschema` in the external dependencies of `serfe_llm_assistant`.
- Test runner runs the container as the `odoo` user.
- `serfe_llm_thread`: bus error in the notification handler patch.
- `serfe_web_json_editor`: `json_inline` widget alias.
- `serfe_llm_assistant`: invalid `attrs` on the ace widget of the prompt views.
