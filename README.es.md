# Importación de facturas de proveedor con IA para Odoo (Argentina)

[English](README.md)

Subí una factura de proveedor (PDF o imagen) a Odoo 16 y obtené un borrador de factura con los datos argentinos (AFIP) ya cargados, listo para revisar. Usa un modelo de lenguaje (ChatGPT u otro) que elegís vos, a través de la API de tu propio proveedor.

## El problema

Cargar a mano las facturas de proveedores es repetitivo: copiar el proveedor, el CUIT, el tipo de comprobante, punto de venta y número, las fechas, el IVA y las percepciones, línea por línea. Lleva tiempo operativo y se presta a errores de tipeo.

## Qué hace

* **Lee la factura** desde un PDF o una imagen y crea un **borrador de factura de proveedor**. Nunca la publica.
* **Entiende facturas argentinas:** el CUIT del proveedor, la letra del comprobante (A, B o C) y el tipo de documento Latam que le corresponde, punto de venta y número como están impresos, fechas día-mes-año, la alícuota de IVA impresa, y las percepciones (IIBB e IVA) aplicadas como el impuesto AFIP correspondiente.
* **Respeta alícuotas inusuales**, como 27% en telecomunicaciones, gas o electricidad, porque las alícuotas de IVA de compras de tu compañía son parte de lo que recibe el modelo.
* **Está pensado para revisarse:** un paso que no se puede resolver deja el borrador tal como fue extraído, en vez de bloquear la importación.
* **Se puede apagar:** archivar el asistente *Invoice Extraction* desactiva la importación con IA y *Upload* vuelve a los decodificadores estándar de Odoo.

## Cómo funciona

1. En la lista de facturas o notas de crédito de proveedor, presioná *Upload* y elegí el PDF o la imagen (o usá *Process with AI* en un borrador existente).
2. Se lee el documento y se extraen los datos con el modelo que configuraste.
3. Se abre un asistente de revisión con el resultado. Verificás totales, impuestos y proveedor, corregís lo necesario y publicás.

Está construido sobre [`account_invoice_import`](https://github.com/OCA/edi) de OCA, así que el reconocimiento de proveedor, producto e impuestos es el estándar.

## Limitaciones

* **Solo Argentina.** La extracción está afinada para comprobantes AFIP (CUIT, letras, impuestos AFIP, `l10n_ar`). Otros países, como Uruguay, no están cubiertos: [contactanos](https://www.serfe.com/) si lo necesitás.
* **Solo Odoo 16 Community.** No se revisaron otras versiones.
* **El modelo puede equivocarse.** El resultado es una sugerencia: verificá totales, impuestos y proveedor antes de publicar. Escaneos de mala calidad o diseños poco comunes pueden dar borradores incompletos.
* **Los proveedores se alcanzan a través de LiteLLM**, un proxy que ejecutás vos delante de tu proveedor de IA.
* **La API key del proveedor se guarda en el registro del proveedor de Odoo y todos los usuarios internos pueden leerla.** Usá una key con presupuesto limitado, o restringí quién tiene acceso como usuario interno.

## Costos y datos

* **Sin costo de licencia.** Los módulos son gratuitos y de código abierto.
* **Tus costos:** el uso de tu proveedor de IA (depende del proveedor, del modelo y del tamaño de los documentos) y el alojamiento de tu proxy LiteLLM. Serfe no provee el servicio de IA.
* **Tus datos:** cada factura se envía al proveedor de IA que configurás a través de tu propio proxy LiteLLM. Serfe no la recibe. Revisá la política de datos de tu proveedor antes de procesar documentos.

## Requisitos

* Odoo 16 Community, con `l10n_ar` para el comportamiento argentino.
* `account_invoice_import` de [OCA/edi](https://github.com/OCA/edi), más los demás repositorios de `oca_dependencies.txt`.
* Una cuenta con un proveedor de IA (OpenAI, Anthropic, Mistral, etc.) y un proxy [LiteLLM](https://github.com/BerriAI/litellm) delante, ambos provistos y operados por vos. LiteLLM funciona con la API de cada proveedor: consultá la [documentación de LiteLLM](https://docs.litellm.ai/) y la de tu proveedor para configurarlo.

## Instalación

1. Clonar este repositorio (rama `16.0`) y los repositorios de `oca_dependencies.txt`.
2. Agregarlos al `addons_path` de Odoo.
3. Instalar las dependencias de Python: `pip install -r requirements.txt`.
4. Actualizar la lista de aplicaciones e instalar `llm_invoice_ocr`; sus dependencias se instalan con él.

## Configuración

1. Abrir *LLM → Configuración → Proveedores*, crear o abrir el proveedor *LiteLLM* (servicio *LiteLLM*) y completar *API Base* (la URL de tu proxy) y *API Key*. Luego usar *Fetch Models* para importar los modelos del proxy.
2. Asignar un modelo al asistente *Invoice Extraction* (*LLM → Configuración → Asistentes*).

Opcionalmente, definí `LITELLM_API_BASE` y `LITELLM_API_KEY` en el entorno del proceso de Odoo antes de instalar, y `llm_litellm_responses` crea el proveedor *LiteLLM* por vos. Ninguna tiene valor por defecto.

## Módulos

La importación de facturas usa estos módulos del repositorio:

| Módulo | Descripción | Origen |
|---|---|---|
| `llm_invoice_ocr` | Ajuste argentino (AFIP) de la importación de facturas | este repo |
| `serfe_account_invoice_import_llm` | Importación de facturas con LLM y OCR | fork de [apexive/odoo-llm](https://github.com/apexive/odoo-llm) `account_invoice_import_llm` |
| `llm_litellm_responses` | API Responses, reintentos de OCR, creación automática del proveedor | este repo |
| `serfe_llm_litellm` | Proveedor LiteLLM | fork de `llm_litellm` |

El resto es la base sobre la que corren, y también sirve para chatear con un modelo desde el chatter de cualquier registro: `serfe_llm`, `serfe_llm_assistant`, `serfe_llm_thread`, `serfe_llm_tool`, `serfe_llm_training`, `serfe_web_json_editor` y `llm_access_groups`. Ver la tabla completa en el [README en inglés](README.md#modules). Los módulos de Apexive conservan su autoría original; los ocho llevan el prefijo `serfe_` para no chocar con los de Apexive en el store de Odoo, así que no hay que instalar ambos. [UPSTREAM.md](UPSTREAM.md) detalla el commit base y los cambios locales.

## Licencia

Mixta, según el módulo. Ver [LICENSE](LICENSE).

## Acerca de

Mantenido por [Serfe](https://www.serfe.com/). Las consultas sobre la configuración o la adaptación de los módulos a tu caso son bienvenidas: contactanos.
