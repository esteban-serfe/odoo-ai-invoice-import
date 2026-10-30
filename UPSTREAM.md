# Upstream

Eight modules are vendored, without history, from
[apexive/odoo-llm](https://github.com/apexive/odoo-llm), branch `16.0`.

* Base commit: `a6a229d94ab5aa2d99d8de88ef290b85284258f3` (tag `a6a229d-vendor`)
* The first commit of this repository holds those modules unmodified. Every
  local change is a separate commit after it (`git log --oneline`), so each one
  can be sent upstream on its own.

## Renamed forks

Apexive publishes `llm_thread`, `llm_litellm` and others under the same technical
names in the Odoo Apps store, so the five modules we had to modify are renamed
with the prefix `serfe_` to avoid clashing with them:

| Upstream name | Name here |
|---|---|
| `llm_thread` | `serfe_llm_thread` |
| `llm_assistant` | `serfe_llm_assistant` |
| `llm_litellm` | `serfe_llm_litellm` |
| `web_json_editor` | `serfe_web_json_editor` |
| `account_invoice_import_llm` | `serfe_account_invoice_import_llm` |

Models, fields, tables and the Python/JS code are unchanged; only the module
name changes (dependencies, external IDs, asset paths, OWL templates, imports,
translation files). Do not install a `serfe_*` module together with the upstream
module of the same name: they define the same models and data.

`llm`, `llm_tool` and `llm_training` are unmodified and keep their names.

## Modified files

Paths are relative to the renamed module directory.

| Module | File | Change |
|---|---|---|
| `serfe_llm_thread` | `static/src/models/messaging_notification_handler.js` | Fix: `this._super(message)` instead of `super._handleNotification(message)` (bus error). Candidate for upstream. |
| `serfe_web_json_editor` | `static/src/fields/json_field.js` | Fix: also register the widget as `json_inline`, the name the llm views use. Candidate for upstream. |
| `serfe_llm_assistant` | `views/llm_assistant_views.xml` | Fix: remove an invalid `attrs` on the ace widget. |
| `serfe_llm_assistant` | `views/llm_prompt_views.xml` | Fix: remove an invalid `attrs` on the ace widget. |
| `serfe_llm_litellm` | `models/http_client.py` | `chat_completion` accepts `**kwargs`. |
| `serfe_llm_litellm` | `models/litellm_provider.py` | Tool calling: message and tool formatting, `tool_choice`, streamed `tool_calls`. |
| `serfe_account_invoice_import_llm` | `__manifest__.py` | Depend on `serfe_llm_litellm` instead of `llm_mistral`. |

Besides these, every file that named a renamed module was updated, and the
manifests add "Serfe" to the authors. Those changes are mechanical.

To list the content changes against the base commit, ignoring the rename:

```
git diff a6a229d-vendor HEAD -M --stat -- llm_thread serfe_llm_thread \
    llm_assistant serfe_llm_assistant llm_litellm serfe_llm_litellm \
    web_json_editor serfe_web_json_editor \
    account_invoice_import_llm serfe_account_invoice_import_llm
```

## Updating

Fetch the upstream branch, diff the eight directories against the base commit
(mapping the five renamed ones to their `serfe_` directory), and merge the
result. Record the new base commit here. Once Apexive accepts the fixes above,
the matching `serfe_` module can be dropped in favour of the upstream one.
