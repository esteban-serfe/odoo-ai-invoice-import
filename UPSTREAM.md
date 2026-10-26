# Upstream

Eight modules are vendored, without history, from
[apexive/odoo-llm](https://github.com/apexive/odoo-llm), branch `16.0`.

* Base commit: `a6a229d94ab5aa2d99d8de88ef290b85284258f3`
* The first commit of this repository holds those modules unmodified. Every
  local change is a separate commit after it (`git log --oneline`), so each one
  can be sent upstream on its own.

## Modified files

| Module | File | Change |
|---|---|---|
| `llm_thread` | `static/src/models/messaging_notification_handler.js` | Fix: `this._super(message)` instead of `super._handleNotification(message)` (bus error). Candidate for upstream. |
| `web_json_editor` | `static/src/fields/json_field.js` | Fix: also register the widget as `json_inline`, the name the llm views use. Candidate for upstream. |
| `llm_assistant` | `views/llm_assistant_views.xml` | Fix: remove an invalid `attrs` on the ace widget. |
| `llm_assistant` | `views/llm_prompt_views.xml` | Fix: remove an invalid `attrs` on the ace widget. |
| `llm_litellm` | `models/http_client.py` | `chat_completion` accepts `**kwargs`. |
| `llm_litellm` | `models/litellm_provider.py` | Tool calling: message and tool formatting, `tool_choice`, streamed `tool_calls`. |
| `account_invoice_import_llm` | `__manifest__.py` | Depend on `llm_litellm` instead of `llm_mistral`. |

Unmodified: `llm`, `llm_tool`, `llm_training`.

To list them again: compare each module directory with the same path at the base
commit, e.g. `git diff 1cfbc17 HEAD --stat -- llm_thread web_json_editor
llm_assistant llm_litellm account_invoice_import_llm`.

## Updating

Fetch the upstream branch, diff the eight directories against the base commit,
and merge the result. Record the new base commit here.
