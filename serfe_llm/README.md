# Base de integración LLM para Odoo

[English](README.en.md)

El módulo fundacional para integrar modelos de lenguaje (LLM) en Odoo. Este módulo base aporta la infraestructura central, la abstracción de proveedores y un sistema de mensajería mejorado sobre el que se apoyan todos los demás módulos LLM del ecosistema.

## Descripción general

La base de integración LLM es el cimiento para construir funciones con IA en las aplicaciones de Odoo. Extiende el sistema de mensajería nativo de Odoo con capacidades específicas de IA y ofrece un marco unificado para conectarse con distintos proveedores de IA.

### Capacidades principales

- **Sistema de mensajería mejorado** - Manejo de mensajes optimizado para IA, con consultas 10 veces más rápidas
- **Abstracción de proveedores** - Interfaz unificada para varios servicios de IA (OpenAI, Anthropic, Ollama, etc.)
- **Gestión de modelos** - Catálogo centralizado de modelos de IA con sus capacidades y metadatos
- **Seguimiento de publicadores** - Gestión de los publicadores y organizaciones de modelos de IA
- **Marco de seguridad** - Control de acceso por roles y gestión de API keys

## Características clave

### Sistema de mensajes de correo mejorado

El módulo extiende el modelo `mail.message` de Odoo con campos específicos de LLM:

```python
# Campo de rol optimizado para rendimiento (consultas 10 veces más rápidas)
llm_role = fields.Selection([
    ('user', 'User'),
    ('assistant', 'Assistant'), 
    ('tool', 'Tool'),
    ('system', 'System')
], compute='_compute_llm_role', store=True, index=True)

# Datos estructurados para los mensajes de herramientas
body_json = fields.Json()
```

### Subtipos de mensaje de IA

Subtipos de mensaje integrados para las interacciones con IA:
- **`serfe_llm.mt_user`**: mensajes del usuario en conversaciones con IA
- **`serfe_llm.mt_assistant`**: respuestas generadas por la IA
- **`serfe_llm.mt_tool`**: resultados y datos de la ejecución de herramientas
- **`serfe_llm.mt_system`**: prompts del sistema y mensajes de configuración

### Marco de proveedores

Abstracción unificada de proveedores que soporta múltiples servicios de IA:

```python
# Despacho dinámico a las implementaciones de cada servicio
provider._dispatch('chat', messages=messages, model=model)
provider._dispatch('embedding', text=text)
provider._dispatch('generate', prompt=prompt, type='image')
```

**Proveedores soportados:**
- **OpenAI** - modelos GPT, DALL-E, embeddings
- **Anthropic** - modelos Claude con tool calling
- **Ollama** - despliegue local de modelos
- **Mistral** - modelos de Mistral AI
- **LiteLLM** - proxy multiproveedor
- **Replicate** - marketplace de modelos
- **FAL.ai** - API de inferencia rápida

### Gestión de modelos

Catálogo completo de modelos con descubrimiento automático:

- **Registro de modelos**: seguimiento centralizado de los modelos de IA disponibles
- **Mapeo de capacidades**: funciones de cada modelo (chat, embedding, multimodal, etc.)
- **Gestión de publicadores**: seguimiento de organizaciones y estado oficial
- **Descubrimiento automático**: función "Fetch Models" para importar modelos automáticamente
- **Selección por defecto**: modelos por defecto configurables según el caso de uso

## Mejoras de rendimiento

### Consultas de mensajes 10 veces más rápidas

El nuevo campo `llm_role` mejora drásticamente el rendimiento:

- **Antes**: joins complejos de subtipos y campos calculados
- **Después**: acceso directo a un campo indexado
- **Resultado**: consultas del historial de conversaciones 10 veces más rápidas

### Operaciones de base de datos optimizadas

- **Campo de rol indexado**: filtrado y ordenamiento rápidos de los mensajes de IA
- **Menor complejidad**: se eliminan las costosas búsquedas de rol
- **Paginación eficiente**: carga optimizada del historial de conversaciones
- **Arquitectura escalable**: el rendimiento se mantiene con grandes volúmenes de datos

## Primeros pasos

### Instalación

1. Instalar el módulo en tu instancia de Odoo
2. Verificar que se cumplan las dependencias (`mail`, `web`)
3. Instalar los módulos de proveedor de los servicios de IA que prefieras

### Configuración básica

1. **Configurar un proveedor de IA:**
   ```
   Ir a: LLM → Configuración → Proveedores
   Crear un proveedor nuevo con las credenciales de la API
   Hacer clic en "Fetch Models" para importar los modelos disponibles
   ```

2. **Configurar los modelos:**
   ```
   Ir a: LLM → Configuración → Modelos
   Definir los modelos por defecto para chat, embedding, etc.
   Configurar los parámetros y capacidades de cada modelo
   ```

3. **Configurar la seguridad:**
   ```
   Asignar los usuarios a los grupos LLM User o LLM Manager
   Configurar los permisos de acceso a las API keys
   Definir los requisitos de consentimiento para herramientas
   ```

## Especificaciones técnicas

### Información del módulo

- **Nombre**: LLM Integration Base
- **Versión**: 16.0.1.3.0
- **Categoría**: Technical
- **Licencia**: LGPL-3
- **Dependencias**: `mail`, `web`
- **Autor**: Apexive Solutions LLC

### Modelos principales

#### `llm.provider`
Gestiona las conexiones con los proveedores de servicios de IA:
- Autenticación y configuración de la API
- Descubrimiento e importación de modelos
- Implementaciones específicas de cada servicio
- Seguimiento y monitoreo del uso

#### `llm.model` 
Representa cada modelo de IA:
- Capacidades y parámetros del modelo
- Información y estado del publicador
- Configuración del modelo por defecto
- Metadatos de rendimiento y costo

#### `llm.publisher`
Registra los publicadores de modelos de IA:
- Información de la organización
- Verificación del estado oficial
- Gestión del portafolio de modelos
- Ajustes propios de cada publicador

#### `mail.message` (extendido)
Con campos específicos de LLM:
- `llm_role`: seguimiento del rol optimizado para rendimiento
- `body_json`: datos estructurados para mensajes de herramientas
- Rol calculado a partir de los subtipos del mensaje
- Manejo de correo específico de IA

### Esquema de base de datos

```sql
-- Optimización de rendimiento: campo de rol indexado
ALTER TABLE mail_message ADD COLUMN llm_role VARCHAR;
CREATE INDEX idx_mail_message_llm_role ON mail_message(llm_role);

-- Almacenamiento de datos estructurados para herramientas
ALTER TABLE mail_message ADD COLUMN body_json JSONB;
```

## Referencia de la API

### Métodos del proveedor

```python
# Chat completion
response = provider.chat(
    messages=[{"role": "user", "content": "Hello"}],
    model="gpt-4",
    stream=False
)

# Embedding de texto
embedding = provider.embedding(
    text="Sample text to embed",
    model="text-embedding-ada-002"
)

# Generación de contenido
content = provider.generate(
    prompt="A beautiful landscape",
    type="image",
    model="dall-e-3"
)
```

### Publicación de mensajes

```python
# Publicación de mensajes optimizada para IA
thread.message_post(
    body="AI response content",
    llm_role="assistant",
    author_id=False
)

# Resultado de una herramienta con datos estructurados
thread.message_post(
    body_json={
        "tool_call_id": "call_123",
        "function": "search_records",
        "result": {"count": 5, "records": [...]}
    },
    llm_role="tool"
)
```

## Patrones de integración

### Extender con nuevos proveedores

1. **Crear un módulo de proveedor:**
   ```python
   class LLMProvider(models.Model):
       _inherit = "llm.provider"
       
       @api.model  
       def _get_available_services(self):
           return super()._get_available_services() + [
               ('my_service', 'My AI Service')
           ]
   ```

2. **Implementar los métodos del servicio:**
   ```python
   def my_service_chat(self, messages, model=None, **kwargs):
       """Implementación de chat específica del servicio"""
       # Detalles de la implementación
       
   def my_service_embedding(self, text, model=None, **kwargs):
       """Implementación de embedding específica del servicio"""
       # Detalles de la implementación
   ```

### Manejo de mensajes personalizado

```python
class CustomThread(models.Model):
    _inherit = "llm.thread"
    
    def message_post(self, **kwargs):
        # Preprocesamiento personalizado
        if kwargs.get('llm_role') == 'custom':
            # Lógica del rol personalizado
            pass
            
        return super().message_post(**kwargs)
```

## Notas de migración

### Desde versiones anteriores

**Migración de subtipos de mensaje:**
- Los subtipos de mensaje pasaron de un módulo separado al módulo base
- La migración automática conserva los datos existentes
- Las mejoras de rendimiento se aplican a los mensajes existentes

**Migración del campo de rol:**
- Cálculo automático de `llm_role` para los mensajes existentes
- La migración de base de datos crea los índices de rendimiento
- Se mantiene la compatibilidad hacia atrás

### Cambios incompatibles

**Versión 16.0.1.3.0:**
- Los subtipos de mensaje pasaron al módulo base
- Se agregó el cálculo obligatorio del campo `llm_role`
- Mecanismo de despacho de proveedores mejorado

## Módulos relacionados

Se pueden armar soluciones de IA completas combinándolo con módulos especializados:

- **`llm_assistant`**: asistentes de IA con gestión de prompts
- **`llm_thread`**: interfaces de chat y gestión de conversaciones
- **`serfe_llm_tool`**: function calling e integración con Odoo
- **`llm_generate`**: API unificada de generación de contenido
- **`llm_knowledge`**: RAG y base de conocimiento
- **`llm_store`**: almacenamiento vectorial y búsqueda por similitud

## Soporte y recursos

- **Documentación**: [repositorio de GitHub](https://github.com/apexive/odoo-llm)
- **Guía de arquitectura**: [OVERVIEW.md](../OVERVIEW.md)
- **Soporte de la comunidad**: [GitHub Discussions](https://github.com/apexive/odoo-llm/discussions)
- **Reporte de errores**: [GitHub Issues](https://github.com/apexive/odoo-llm/issues)

## Licencia

Este módulo está licenciado bajo [LGPL-3](https://www.gnu.org/licenses/lgpl-3.0.html).

---

*© 2025 Apexive Solutions LLC. Todos los derechos reservados.*
