# llm_litellm_responses

Español · [English](README.en.md)

Módulo de Odoo 16 que extiende `serfe_llm_litellm` con la API Responses de LiteLLM, OCR mediante archivos de entrada y creación automática del proveedor. No modifica `serfe_llm_litellm`: todo se hace con `_inherit` y una subclase del cliente.

## Para qué sirve
- **Alta automática del proveedor:** al instalar, crea o actualiza un `llm.provider` llamado `LiteLLM` (servicio `litellm`, compañía actual, activo) a partir del entorno.
- **`chat_completion()` sin streaming** devuelve el dict ya parseado en lugar de un generador.
- **API Responses:** los modelos con `model_info.mode == "responses"` se enrutan por `/responses`, salvo cuando hay herramientas, en cuyo caso se usa `/chat/completions`.
- **Mensajes de herramienta huérfanos:** se eliminan antes de enviar, evitando errores "No tool call found for function call output".
- **OCR** mediante `input_file` / `input_image` de la API Responses, con hasta 3 reintentos ante errores transitorios `invalid_file`.
- **Información del modelo:** el listado de modelos se enriquece con `model_info` de `/model/info` de LiteLLM, y el asistente *Fetch Models* lo copia a `llm.model.model_info`.

## Requisitos / Dependencias
- Odoo 16 (Community)
- Módulos de Odoo: `serfe_llm_litellm`
- Un proxy [LiteLLM](https://github.com/BerriAI/litellm) accesible y una API key para él

## Instalación
1. Poner el addon y `serfe_llm_litellm` en el `addons_path`.
2. Instalar el módulo (Aplicaciones, o `-i llm_litellm_responses`).
3. Configurar el proveedor desde la interfaz (*LLM → Configuración → Proveedores*: *API Base* y *API Key*), o definir las variables de entorno opcionales de abajo en el proceso de Odoo **antes** de instalar para que el proveedor se cree solo.

Si falta `LITELLM_API_BASE` o `LITELLM_API_KEY`, la instalación registra una advertencia y omite la creación del proveedor sin fallar (útil para bases de test/CI). Crear el proveedor a mano, o definir ambas variables y reinstalar.

## Configuración

| Variable | Descripción |
|---|---|
| `LITELLM_API_BASE` | URL base del proxy LiteLLM. Opcional, sin valor por defecto. Se quita la `/` final. |
| `LITELLM_API_KEY` | API key del proxy LiteLLM. Opcional. |

Se necesitan ambas juntas para crear el proveedor al instalar. No se leen en tiempo de ejecución: después de instalar, la fuente de verdad es el registro del proveedor.

## Seguridad / Acceso
No agrega grupos, ACLs ni reglas de registro. La API key se guarda en `llm.provider` como un campo común, y todos los usuarios internos pueden leer ese modelo, así que la key no está oculta para ellos.

## Multicompañía
El proveedor se crea para la compañía activa al momento de instalar (`env.company`).

## Licencia
LGPL-3
