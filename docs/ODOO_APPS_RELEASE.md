# Odoo Apps release audit — Argentina Invoice OCR

Target: Odoo 16 Community, branch `16.0`, addon `serfe_invoice_ocr`
`16.0.1.1.0`, published by Serfe. No remote changes or store submission were made.

## Requirements checked

Read the live [Vendor Guidelines](https://apps.odoo.com/apps/vendor-guidelines)
and [FAQ](https://apps.odoo.com/apps/faq). Both were reachable. They require
valid manifests and dependencies, accurate English listings and screenshots,
allowed local media, no scripts or promotional external links, compatible
licenses, and disclosure and prior opt-in for external customer-data transfers.
The main listing has a redacted English screenshot, PNG icon and cover, no external links
or scripts, and explicit provider, data and cost disclosure. The addon is free
(no `price`), requires no activation key, and uses a customer-configured endpoint.
It prepares draft bills with Argentine localization and does not use Odoo
Enterprise OCR or call AFIP to verify the documents.

### Addon graph and attribution

| Addon | Direct dependencies | License |
|---|---|---|
| `serfe_invoice_ocr` | `apx_account_invoice_import_llm`, `apx_llm_litellm`, `l10n_ar` | AGPL-3 |
| `apx_account_invoice_import_llm` | OCA `account_invoice_import`, `apx_llm_assistant`, `apx_llm_litellm` | AGPL-3 |
| `apx_llm_assistant` | `base`, `mail`, `web`, `apx_llm`, `apx_llm_thread`, `apx_llm_tool`, `apx_web_json_editor` | LGPL-3 |
| `apx_llm_thread` | `base`, `mail`, `web`, `apx_llm`, `apx_llm_tool` | LGPL-3 |
| `apx_llm_tool` | `base`, `mail`, `apx_llm` | LGPL-3 |
| `apx_llm_litellm` | `apx_llm` | LGPL-3 |
| `apx_llm` | `mail`, `web` | LGPL-3 |
| `apx_web_json_editor` | `web` | LGPL-3 |
| `apx_llm_training` | `base`, `mail`, `apx_llm` | LGPL-3 |
| `serfe_llm_access_groups` | `apx_llm_assistant`, `apx_llm_thread`, `apx_llm_training` | LGPL-3 |

Training and Serfe access groups are optional for OCR. The official 16.0
[OCA Invoice Import listing](https://apps.odoo.com/apps/modules/16.0/account_invoice_import)
lists the transitive OCA addons (`base_business_document_import`, `pdf_helper`,
`account_tax_unece`, `uom_unece`, `base_unece`). No OCA source is bundled here.
Install from the repositories in `oca_dependencies.txt` and install the server
packages in `requirements.txt`. See `LICENSE` and `UPSTREAM.md` for the
existing Apexive attribution and license texts. Do not install these forks
alongside the corresponding upstream technical modules on the same database.

## Changes and upgrade impact

- Added administrator-only, per-company opt-in. It defaults off on fresh
  installs and upgrades, is not copied to duplicate companies, and is checked
  at extraction time. Vendor upload without consent still uses Odoo's core
  decoders; non-AI OCA parsing remains available while the assistant is active.
  The bill button checks write access and only accepts draft vendor bills or
  refunds; the server does not rely on form visibility for enforcement.
- Restricted ORM access to the LiteLLM API key to LLM Managers and removed
  credential copying. Normal accounting users can still use the controlled
  invoice workflow. Direct provider usage requires LLM Manager or the
  optional LLM Chatter group. The endpoint and model remain shared as
  configured; do not share one across companies with incompatible policies.
- Removed the implicit localhost destination, disabled HTTP redirects, set
  connection/read timeouts and stopped forwarding verbatim provider errors.
  The invoice path accepts PDF, PNG and JPEG up to 20 MiB and rejects
  non-finite extracted amounts. It closes OCR streams and uses no LLM tools.
- Sandboxed shared Jinja rendering and disabled the generic arbitrary method
  execution tool in the bundled chat framework. Its XML ID and implementation
  selection value remain for existing databases. Other chat tools are not part
  of invoice extraction. Provider secrets are not encrypted at rest by this
  addon. Restrict egress at the network layer and use HTTPS outside a trusted
  private network.
- Preserved module technical names, existing XML IDs and licenses. The company
  consent field is additive. `l10n_ar` is now a declared dependency; admins
  still need to configure the correct company chart and AFIP settings.

Back up the database and filestore. Deploy the dependency versions together
and upgrade `apx_llm`, `apx_llm_litellm`, `apx_llm_thread`, `apx_llm_tool`,
`apx_llm_assistant`, `apx_account_invoice_import_llm`, and `serfe_invoice_ocr`.
If installed, also upgrade `serfe_llm_access_groups` in the same operation.
Rotate previously configured API keys since legacy internal users had read
access. Re-enable each participating company explicitly after reviewing
the configured endpoint and its downstream providers.

## Validation

- Baseline (`d32a995`): 34 tests passed.
- Release clean install: **42 tests passed** in Odoo 16 / PostgreSQL 15
  using `bash scripts/run-tests.sh`. The container network blocks external
  calls; provider responses are mocked. Includes A/B/C LATAM document mapping,
  numbering, and B/C VAT treatment; the OCA wizard and manual fallback;
  opt-in and revocation, access checks, API-key protection, redirect refusal,
  timeout sanitization, and PDF/image transport.
- Upgrade without demo data from `d32a995`: verified the existing provider
  XML ID, configured API base and fixture key were retained, `l10n_ar` was
  installed, and no existing company was opted in automatically.
- Static checks passed: ten manifest literals and referenced data files,
  local listing media and HTML tags, Python and XML parsing, shell syntax,
  and `git diff --check`. The local pre-commit launcher was unavailable
  (missing interpreter); the full pre-commit suite was not run.
- OCA revisions tested: `edi` `cb22116d4e858e043133f5780d7da7b12023133e`;
  `community-data-files` `8e47e43ff7597b66d3488264d6d20d36f5c114bb`.
  The existing Docker runner tracks their `16.0` branches. GitHub Actions
  now runs the same offline tests on pushes and pull requests.

## Remaining gates before submission

1. Use synthetic Argentine bills with an approved live endpoint. Test PDF
   and image uploads and the draft button, then check CUIT matching, VAT
   (including 27%), IIBB/VAT perceptions, charges, totals and credit notes
   on a configured Argentine company. Mocked responses do not validate
   provider quality or a specific deployment's accounting setup.
2. Preview the English listing, screenshot readability and dependency
   resolution in the actual Apps scanner. The public dependency page and
   guidelines are verified; scanner acceptance, any technical-name conflicts,
   the treatment of the bundled upstream minified JSONEditor asset, and Odoo's
   Enterprise-clone policy decision are not independently verifiable locally.
3. Have Serfe approve the privacy/support copy and provider guidance. Review
   separate Apexive-derived companion listings before advertising them as
   independent apps; their general chat/tool/training workflows are not the
   invoice OCR release scope. Confirm publisher ownership and repository access.
