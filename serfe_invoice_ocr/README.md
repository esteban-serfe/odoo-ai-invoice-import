# serfe_invoice_ocr

Español · [English](README.en.md)

Módulo de Odoo 16 que afina la importación de facturas con IA para comprobantes de proveedor argentinos (AFIP). Está enfocado en Argentina; otros países no están cubiertos, contactá a Serfe si lo necesitás. Lee el PDF o la imagen de una factura de proveedor con un LLM y crea un borrador de factura para revisar.

## Para qué sirve

Extiende `apx_account_invoice_import_llm` para que use el proveedor de IA de `serfe_llm_litellm_responses` y entienda comprobantes AFIP.

- **Un solo proveedor para OCR y extracción:** la factura se transcribe y analiza con el modelo configurado en el asistente *Invoice Extraction*, en lugar del proveedor de OCR por defecto.
- **Prompt argentino:** el prompt del asistente se reemplaza por uno afinado para comprobantes AFIP. Primero decide si el documento es realmente una factura, lee el CUIT del proveedor, interpreta las fechas día-mes-año, extrae punto de venta y número tal como están impresos, la letra del comprobante (A/B/C) y los cargos a nivel documento. Pide la alícuota de IVA impresa con su evidencia en lugar de una recordada.
- **Alícuotas de IVA de la compañía en el prompt:** se agregan al prompt las alícuotas de IVA de compras configuradas para la compañía, para que las inusuales (como 27% en telecomunicaciones, gas o electricidad) no se reemplacen por una común. Solo para compañías argentinas con `l10n_ar`.
- **Tipo y número de documento:** la letra detectada selecciona el tipo de documento Latam y el número. Para las letras B y C todas las líneas reciben *IVA No Corresponde*, como exige `l10n_ar`.
- **Corrección del porcentaje de IVA:** la alícuota implícita en el subtotal y el total extraídos reemplaza la de las líneas cuando no coinciden. Solo se aplica si todas las líneas coinciden en un único impuesto de IVA.
- **Percepciones como impuestos:** *Percepción IIBB / IVA* se aplican como el impuesto tributo AFIP correspondiente sobre las líneas existentes.
- **Mejor esfuerzo:** cualquier paso que no pueda resolverse deja el borrador tal como fue extraído para revisión manual. Nunca bloquea la importación.
- **Botón Subir:** en facturas y notas de crédito de proveedor, *Upload* abre el asistente de revisión. Otras listas usan los decodificadores de documentos estándar de Odoo.
- **Desactivación:** archivar el asistente *Invoice Extraction* deshabilita la importación con IA. Desaparecen el botón *Process with AI* y el menú *Import Vendor Bills*, el asistente se niega a abrirse y *Upload* crea la factura con los decodificadores estándar y muestra un aviso.
- **Mensajes:** los errores de protección de *Process with AI* son traducibles.

## Requisitos / Dependencias
- Odoo 16 (Community)
- Módulos de Odoo: `serfe_llm_litellm_responses`, `apx_account_invoice_import_llm`, `apx_llm_litellm`
- Opcional: `l10n_ar` para el comportamiento argentino
- Una cuenta con un proveedor de IA, provista por vos.

## Instalación
1. Poner el addon y sus dependencias en el `addons_path`.
2. Instalar `serfe_llm_litellm_responses` y configurar el proveedor desde la interfaz (*LLM → Configuración → Proveedores*): completar *API Base* y *API Key* con los datos de tu proveedor de IA. El módulo se conecta a la API de tu proveedor: consultá su documentación para obtener la URL de la API y la clave. Si preferís, contactá a Serfe y te ayudamos.
3. Traer los modelos de ese proveedor (*Fetch Models* en el formulario del proveedor).
4. Instalar el módulo (Aplicaciones, o `-i serfe_invoice_ocr`).

Si ya existe un modelo en el proveedor, la instalación lo asigna al asistente *Invoice Extraction*. Si no, solo registra una advertencia: asignar un modelo al asistente en *LLM → Configuración → Asistentes*, o actualizar el módulo una vez traído un modelo.

## Configuración
No tiene variables de entorno ni parámetros de sistema propios. La configuración es el modelo del asistente *Invoice Extraction* y los ajustes del proveedor de `serfe_llm_litellm_responses`.

## Seguridad / Acceso
- No agrega grupos, ACLs ni reglas de registro; rigen los permisos estándar de contabilidad.
- El documento de la factura se envía al proveedor de IA que configuraste. Serfe no lo recibe.
- La salida de la IA es una sugerencia: totales, impuestos y proveedor deben verificarse antes de publicar.

## Multicompañía
Las alícuotas de IVA y el impuesto *IVA No Corresponde* se leen de la compañía de la factura, de modo que cada compañía usa sus propios impuestos. El prompt nombra a la compañía que importa y su CUIT para que el modelo no la confunda con el proveedor. El asistente y el proveedor se comparten tal como estén configurados.

## Licencia
AGPL-3 (depende de `apx_account_invoice_import_llm`, que es AGPL-3).
