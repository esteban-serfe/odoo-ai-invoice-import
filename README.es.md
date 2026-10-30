# odoo-ai-addons

[English](README.md)

Addons de Odoo 16 para chatear con LLMs, restringir quién puede usarlos e importar facturas de proveedor con IA, a través de un proxy LiteLLM.

## Características principales

* Chat con un LLM desde el chatter de cualquier registro, con asistentes, prompts y herramientas.
* Proveedor LiteLLM con la API Responses, tool calling y OCR con reintentos.
* Control de acceso: un grupo dedicado *LLM Chatter* y menús de configuración de LLM limitados a *LLM Manager*.
* Importación de facturas de proveedor desde PDF o imagen con un LLM, afinada para comprobantes argentinos (AFIP).

## Alcance

La importación de facturas está enfocada en Argentina (CUIT, letras de comprobante, impuestos AFIP, `l10n_ar`). Otros países, como Uruguay, no están cubiertos: [contactanos](https://www.serfe.com/) si lo necesitás.

## Requisitos

* Odoo 16 Community.
* `account_invoice_import` de [OCA/edi](https://github.com/OCA/edi), más los demás repositorios de `oca_dependencies.txt`.
* Una cuenta con un proveedor de IA (OpenAI, Anthropic, Mistral, etc.) y un proxy [LiteLLM](https://github.com/BerriAI/litellm) delante, ambos provistos y operados por vos. Serfe no provee el servicio de IA. LiteLLM funciona con la API de cada proveedor: consultá la [documentación de LiteLLM](https://docs.litellm.ai/) y la de tu proveedor para configurarlo.
* La URL y la API key de tu proxy LiteLLM. Se cargan en el proveedor *LiteLLM* desde la interfaz de Odoo (ver Configuración). Opcionalmente, podés pasarlas como variables de entorno del proceso de Odoo para que el proveedor se cree al instalar:

| Variable | Descripción |
|---|---|
| `LITELLM_API_BASE` | URL de tu proxy LiteLLM. Opcional, no tiene valor por defecto. |
| `LITELLM_API_KEY` | API key de tu proxy LiteLLM. Opcional. |

## Módulos

Ver la tabla de módulos en el [README en inglés](README.md#modules). Cada módulo tiene su propio README. [UPSTREAM.md](UPSTREAM.md) detalla el commit base y los cambios locales de los módulos vendorizados.

## Instalación

1. Clonar este repositorio (rama `16.0`) y los repositorios de `oca_dependencies.txt`.
2. Agregarlos al `addons_path` de Odoo.
3. Instalar las dependencias de Python: `pip install -r requirements.txt`.
4. Actualizar la lista de aplicaciones e instalar los módulos que necesites.
5. Opcional: si `LITELLM_API_BASE` y `LITELLM_API_KEY` están definidas en el entorno del proceso de Odoo, `llm_litellm_responses` crea el proveedor *LiteLLM* al instalarse. Sin ellas se instala normalmente y el proveedor se configura desde la interfaz.

## Configuración

1. Abrir *LLM → Configuración → Proveedores*, crear o abrir el proveedor *LiteLLM* (servicio *LiteLLM*) y completar *API Base* (la URL de tu proxy) y *API Key*. Omitir si el proveedor ya se creó con las variables de entorno. Luego usar *Fetch Models* para importar los modelos del proxy.
2. Asignar un modelo al asistente *Invoice Extraction* (*LLM → Configuración → Asistentes*) para habilitar `llm_invoice_ocr`.
3. Agregar a los usuarios que pueden chatear con el LLM al grupo *User: LLM Chatter* (`llm_access_groups`). *LLM Manager* lo incluye.

## Licencia

Mixta, según el módulo. Ver [LICENSE](LICENSE).

## Acerca de

Mantenido por [Serfe](https://www.serfe.com/). Las consultas sobre la configuración o la adaptación de los módulos a tu caso son bienvenidas: contactanos.
