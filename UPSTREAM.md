# Upstream

Eight modules are vendored, without history, from
[apexive/odoo-llm](https://github.com/apexive/odoo-llm), branch `16.0`.

* Base commit: `a6a229d94ab5aa2d99d8de88ef290b85284258f3` (tag `a6a229d-vendor`)
* The first commit of this repository holds those modules unmodified. Every
  local change is a separate commit after it (`git log --oneline`), so each one
  can be sent upstream on its own.

## Renamed modules

Apexive publishes `llm`, `llm_thread`, `llm_litellm` and others under the same technical
names in the Odoo Apps store, where a technical name belongs to a single vendor. All
eight modules are renamed with the prefix `apx_` (for Apexive). The `serfe_` prefix is
kept for the modules written by Serfe, so the name tells which is which:

| Upstream name | Name here | Modified |
|---|---|---|
| `llm` | `apx_llm` | no |
| `llm_thread` | `apx_llm_thread` | yes |
| `llm_tool` | `apx_llm_tool` | no |
| `llm_assistant` | `apx_llm_assistant` | yes |
| `llm_litellm` | `apx_llm_litellm` | yes |
| `llm_training` | `apx_llm_training` | no |
| `web_json_editor` | `apx_web_json_editor` | yes |
| `account_invoice_import_llm` | `apx_account_invoice_import_llm` | yes |

Models, fields, tables and the Python/JS code are unchanged; only the module
name changes (dependencies, external IDs, asset paths, OWL templates, imports,
translation files). Do not install an `apx_*` module together with the upstream
module of the same name: they define the same models and data.

## Modified files

Paths are relative to the renamed module directory.

| Module | File | Change |
|---|---|---|
| `apx_llm_thread` | `static/src/models/messaging_notification_handler.js` | Fix: `this._super(message)` instead of `super._handleNotification(message)` (bus error). Candidate for upstream. |
| `apx_web_json_editor` | `static/src/fields/json_field.js` | Fix: also register the widget as `json_inline`, the name the llm views use. Candidate for upstream. |
| `apx_llm_assistant` | `views/llm_assistant_views.xml` | Fix: remove an invalid `attrs` on the ace widget. |
| `apx_llm_assistant` | `views/llm_prompt_views.xml` | Fix: remove an invalid `attrs` on the ace widget. |
| `apx_llm_litellm` | `models/http_client.py` | `chat_completion` accepts `**kwargs`. |
| `apx_llm_litellm` | `models/litellm_provider.py` | Tool calling: message and tool formatting, `tool_choice`, streamed `tool_calls`. |
| `apx_account_invoice_import_llm` | `__manifest__.py` | Depend on `apx_llm_litellm` instead of `llm_mistral`. |

Besides these, every file that named a renamed module was updated, the
manifests add "Serfe" to the authors, and the icons are replaced with Serfe's. Those changes are mechanical.

`apx_account_invoice_import_llm` also has a rewritten README and store description: the upstream ones described Mistral OCR and made claims about accuracy and savings that do not apply here. Its `doc/index.rst` and the Mistral and ChatGPT screenshots were removed.

To list the content changes against the base commit, ignoring the rename:

```
git diff a6a229d-vendor HEAD -M --stat
```

## Updating

Fetch the upstream branch, diff the eight directories against the base commit
(mapping each one to its `apx_` directory), and merge the
result. Record the new base commit here. Once Apexive accepts the fixes above,
the matching `apx_` module can be dropped in favour of the upstream one.
