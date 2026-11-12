# llm_litellm_responses

[Español](README.md) · English
Odoo 16 module that extends `serfe_llm_litellm` with the LiteLLM Responses API, OCR through file inputs, and automatic provider creation. It leaves `serfe_llm_litellm` untouched: everything is done through `_inherit` and a client subclass.

## What is this for?
- **Provider auto-provisioning:** on install, creates or updates an `llm.provider` named `LiteLLM` (service `litellm`, current company, active) from the environment.
- **Non-streaming `chat_completion()`** returns the parsed dict instead of a generator.
- **Responses API:** models with `model_info.mode == "responses"` are routed through `/responses`, except when tools are present, in which case `/chat/completions` is used.
- **Orphaned tool messages** are stripped before sending, avoiding "No tool call found for function call output" errors.
- **OCR** through the Responses API `input_file` / `input_image`, retrying up to 3 times on transient `invalid_file` errors.
- **Model info:** model listing is enriched with `model_info` from LiteLLM's `/model/info`, and the *Fetch Models* wizard copies it onto `llm.model.model_info`.

## Requirements / Dependencies
- Odoo 16 (Community)
- Odoo modules: `serfe_llm_litellm`
- A reachable [LiteLLM](https://github.com/BerriAI/litellm) proxy and an API key for it

## Installation
1. Make the addon and `serfe_llm_litellm` available in your addons path.
2. Install the module (Apps, or `-i llm_litellm_responses`).
3. Configure the provider from the UI (*LLM → Configuration → Providers*: *API Base* and *API Key*), or set the optional environment variables below in the Odoo process **before** installing so the provider is created for you.

If `LITELLM_API_BASE` or `LITELLM_API_KEY` is missing, the install logs a warning and skips the provider creation without failing (useful for test/CI databases). Create the provider by hand, or set both variables and reinstall.

## Configuration

| Variable | Description |
|---|---|
| `LITELLM_API_BASE` | LiteLLM proxy base URL. Optional, there is no default. A trailing `/` is stripped. |
| `LITELLM_API_KEY` | API key for the LiteLLM proxy. Optional. |

Both are needed together to create the provider on install. They are not read at runtime: after install the provider record is the source of truth.

## Security / Access
No groups, ACLs or record rules are added. The API key is stored on `llm.provider` as a plain field, and every internal user can read that model, so the key is not hidden from them.

## Multi-company behavior
The provider is created for the company active at install time (`env.company`).

## Licence
LGPL-3
