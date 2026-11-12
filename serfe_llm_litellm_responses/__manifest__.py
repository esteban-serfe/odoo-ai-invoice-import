{
    "name": "Serfe LiteLLM Responses",
    "version": "16.0.1.0.0",
    "summary": "LiteLLM Responses API, OCR retries and provider auto-provisioning "
    "on top of apx_llm_litellm",
    "description": """
Extends the LiteLLM provider with the Responses API, OCR through file inputs
with retries, and optional provider creation from environment variables.

Data notice: the documents and prompts are sent to the AI provider that you
configure through your own LiteLLM proxy. The module does not send data to
Serfe or to any fixed service.
    """,
    "author": "Serfe",
    "license": "LGPL-3",
    "category": "Technical",
    "depends": ["apx_llm_litellm"],
    "installable": True,
    "application": False,
    "post_init_hook": "post_init_hook",
}
