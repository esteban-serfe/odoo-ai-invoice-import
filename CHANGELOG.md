# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Vendored from apexive/odoo-llm at `a6a229d`: `llm`, `llm_thread`, `llm_tool`, `llm_assistant`, `llm_litellm`, `llm_training`, `web_json_editor`, `account_invoice_import_llm`.
- `llm_litellm_responses`: Responses API, orphaned tool message cleanup, OCR with retries, `model_info`, provider auto-provisioning from `LITELLM_API_BASE` and `LITELLM_API_KEY`.
- `llm_access_groups`: *LLM Chatter* group, LLM menus limited to *LLM Manager*, chatter "AI" button hidden from other users.
- `llm_invoice_ocr`: Argentine (AFIP) extension of `account_invoice_import_llm`.
- Self-contained test runner (`scripts/run-tests.sh`) and lint configuration.

### Changed

- `llm_litellm`: tool calling and extra chat completion parameters.
- `account_invoice_import_llm`: depends on `llm_litellm` instead of `llm_mistral`.

### Fixed

- `llm_thread`: bus error in the notification handler patch.
- `web_json_editor`: `json_inline` widget alias.
- `llm_assistant`: invalid `attrs` on the ace widget of the prompt views.
