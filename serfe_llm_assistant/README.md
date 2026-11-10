# Asistente LLM para Odoo

[English](README.en.md)

Gestión avanzada de asistentes de IA con plantillas de prompts integradas, capacidades de prueba y una orquestación inteligente de la configuración. Este módulo es la capa de inteligencia que define cómo los datos de Odoo se conectan con los modelos de IA.

## Descripción general

El módulo LLM Assistant ofrece una gestión de asistentes de IA que va mucho más allá de un simple chatbot. Es la capa de configuración inteligente que orquesta cómo los modelos de IA interactúan con los datos de Odoo, con gestión integrada de plantillas de prompts y capacidades de prueba completas.

### Capacidades principales

- **Configuración de asistentes de IA** - Definir personas de IA especializadas con roles y capacidades específicas
- **Gestión integrada de prompts** - Sistema consolidado de plantillas de prompts (antes el módulo separado `llm_prompt`)
- **Pruebas de plantillas** - Asistente de pruebas integrado para validar y optimizar prompts
- **Orquestación de contexto** - Mapeo inteligente entre los datos de Odoo y las entradas de la IA
- **Gestión de herramientas** - Configurar las herramientas disponibles y sus patrones de uso
- **Configuración de generación** - Plantillas para distintos tipos de contenido (texto, imágenes, etc.)

## Características clave

### Arquitectura consolidada

La **versión 16.0.1.4.0** consolida la funcionalidad del antiguo módulo `llm_prompt`:

- ✅ **Plantillas de prompts integradas** en la gestión de asistentes
- ✅ **Asistente de pruebas mejorado** con simulación de contexto  
- ✅ **Interfaz simplificada** con selección unificada de asistente y prompt
- ✅ **Detección automática de argumentos** de las variables de la plantilla
- ✅ **Sincronización de esquemas** entre plantillas y formularios

### Tipos de asistente y casos de uso

#### 1. Asistentes de chat
Configurar una IA conversacional con personas específicas:
```python
# Asistente de atención al cliente
assistant = env['llm.assistant'].create({
    'name': 'Customer Support Bot',
    'role': 'Customer Service Representative',
    'goal': 'Provide helpful and accurate customer support',
    'background': 'Expert in our products with access to CRM data',
    'instructions': '''
        - Always be polite and professional
        - Use customer history to provide personalized responses
        - Escalate complex issues to human agents
        - Provide clear, actionable solutions
    ''',
    'tool_ids': [(6, 0, [crm_tool.id, knowledge_tool.id])]
})
```

#### 2. Asistentes de generación de contenido
Configurar flujos especializados de creación de contenido:
```python
# Generador de contenido de marketing
assistant = env['llm.assistant'].create({
    'name': 'Marketing Content Creator',
    'role': 'Marketing Specialist',
    'goal': 'Create compelling marketing content from product data',
    'prompt_id': marketing_template.id,
    'default_values': {
        'brand_voice': 'professional yet approachable',
        'target_audience': 'business professionals'
    }
})
```

#### 3. Asistentes de análisis
Configurar el análisis de datos y la obtención de conclusiones:
```python
# Asistente de inteligencia de negocios
assistant = env['llm.assistant'].create({
    'name': 'BI Analyst',
    'role': 'Business Intelligence Analyst', 
    'goal': 'Analyze business data and provide actionable insights',
    'tool_ids': [(6, 0, [reporting_tool.id, analytics_tool.id])]
})
```

### Sistema integrado de plantillas de prompts

#### Gestión de plantillas
```python
# Crear una plantilla de prompt con detección automática
prompt = env['llm.prompt'].create({
    'name': 'Sales Email Generator',
    'template': '''
Generate a personalized sales email for {{customer_name}} 
regarding {{product_name}}. 

Customer Context:
- Company: {{customer_company}}
- Industry: {{industry}}
- Previous purchases: {{purchase_history}}

Email should be {{tone}} and focus on {{key_benefits}}.
    ''',
    'format': 'text',
    'category_id': sales_category.id
})

# Los argumentos se detectan solos y se genera el esquema
prompt.auto_detect_arguments()
```

#### Formatos avanzados de plantilla

**Formato YAML** para conversaciones estructuradas:
```yaml
messages:
  - type: system
    content: |
      You are {{role}}. Your goal is {{goal}}.
      Customer: {{customer_name}} ({{customer_company}})
  - type: user  
    content: |
      {{user_request}}
```

**Formato JSON** para compatibilidad directa con la API:
```json
{
  "messages": [
    {
      "type": "system",
      "content": "You are {{role}} helping {{customer_name}}"
    },
    {
      "type": "user", 
      "content": "{{user_input}}"
    }
  ],
  "temperature": {{temperature}},
  "max_tokens": {{max_tokens}}
}
```

### Pruebas y validación

#### Asistente de pruebas mejorado

El asistente de pruebas integrado ofrece una validación completa:

```python
# Abrir el asistente de pruebas
wizard = env['llm.assistant.test.wizard'].create({
    'assistant_id': assistant.id,
    'test_context': {
        'customer_name': 'John Smith',
        'customer_company': 'Acme Corp',
        'product_name': 'Enterprise Software'
    }
})

# Probar con distintos escenarios
wizard.run_test_scenarios([
    {'tone': 'professional', 'urgency': 'high'},
    {'tone': 'friendly', 'urgency': 'low'},
    {'tone': 'formal', 'urgency': 'medium'}
])
```

#### Funciones de detección automática

- **Argumentos de la plantilla**: detecta automáticamente las `{{variables}}` de las plantillas
- **Generación de esquemas**: crea esquemas JSON para generar formularios
- **Validación**: asegura la consistencia entre plantilla y esquema
- **Valores por defecto**: valores por defecto inteligentes según el contexto

### Orquestación de contexto

#### Configuración del mapeo de datos

```python
def prepare_context(self, record=None, user_input=None):
    """Transforma los datos de Odoo en un contexto compatible con el LLM"""
    context = {}
    
    if record and record._name == 'sale.order':
        context.update({
            'customer_name': record.partner_id.name,
            'order_total': record.amount_total,
            'order_date': record.date_order,
            'sales_person': record.user_id.name
        })
    
    # Agregar la entrada del usuario y el contexto del sistema
    context['user_input'] = user_input
    context['current_date'] = fields.Date.today()
    
    return context
```

#### Gestión inteligente del historial

```python
def trim_conversation_history(self, messages, max_tokens=4000):
    """Gestión inteligente de la ventana de contexto"""
    # Conservar el mensaje del sistema y el contexto reciente
    # Eliminar los mensajes más antiguos preservando el contexto importante
    # Mantener la coherencia de la conversación
```

## Guía de configuración

### 1. Configuración básica de un asistente

```python
# Crear un asistente especializado
assistant = env['llm.assistant'].create({
    'name': 'Sales Assistant',
    'role': 'Sales Representative',
    'goal': 'Help close deals and provide product information',
    'background': 'Expert in our product portfolio with CRM access',
    'instructions': '''
        Key behaviors:
        - Always qualify leads before pitching
        - Use customer data to personalize responses  
        - Focus on value propositions
        - Suggest appropriate products based on needs
    ''',
    'provider_id': openai_provider.id,
    'model_id': gpt4_model.id,
    'tool_ids': [(6, 0, [crm_search.id, product_catalog.id])]
})
```

### 2. Integración de plantillas de prompts

```python
# Crear una plantilla para el asistente
template = env['llm.prompt'].create({
    'name': 'Sales Conversation Template',
    'template': '''
You are {{role}} working with {{customer_name}} from {{customer_company}}.

Customer Profile:
- Industry: {{industry}}
- Size: {{company_size}}  
- Budget Range: {{budget_range}}
- Key Pain Points: {{pain_points}}

Your goal: {{goal}}

Guidelines: {{instructions}}
    ''',
    'arguments_json': {
        'customer_name': {'type': 'string', 'required': True},
        'customer_company': {'type': 'string', 'required': True},
        'industry': {'type': 'string', 'required': False},
        'budget_range': {'type': 'string', 'required': False}
    }
})

# Vincular la plantilla al asistente
assistant.prompt_id = template.id
```

### 3. Configuración de herramientas

```python
# Configurar las herramientas disponibles para el asistente
assistant.tool_ids = [(6, 0, [
    crm_search_tool.id,      # Buscar registros del CRM
    product_catalog_tool.id,  # Acceder a la información de productos
    pricing_tool.id,         # Obtener precios y descuentos
    calendar_tool.id,        # Agendar reuniones
    email_tool.id           # Enviar correos de seguimiento
])]
```

## Referencia de la API

### Métodos del asistente

```python
# Obtener el prompt del sistema con contexto
system_prompt = assistant.get_system_prompt(context={
    'customer_name': 'John Doe',
    'customer_company': 'ABC Corp'
})

# Preparar el contexto de la conversación
context = assistant.prepare_context(
    record=sale_order,
    user_input="Tell me about pricing options"
)

# Obtener las herramientas disponibles
tools = assistant.get_available_tools()

# Renderizar la plantilla del prompt
messages = assistant.prompt_id.get_messages(arguments={
    'customer_name': 'John Doe',
    'role': 'Sales Assistant'
})
```

### Métodos de la plantilla

```python
# Detectar automáticamente los argumentos de la plantilla
prompt.auto_detect_arguments()

# Renderizar la plantilla con argumentos
rendered = prompt.get_messages(arguments={
    'customer_name': 'John Smith',
    'product_name': 'Enterprise Suite'
})

# Validar la sintaxis de la plantilla
is_valid, errors = prompt.validate_template()
```

## Ejemplos de integración

### Integración con CRM

```python
class SaleOrder(models.Model):
    _inherit = 'sale.order'
    
    def create_ai_assistant_thread(self):
        """Crea un hilo con el asistente de IA para este pedido de venta"""
        thread = self.env['llm.thread'].create({
            'name': f'Sales Discussion - {self.name}',
            'model': self._name,
            'res_id': self.id,
            'assistant_id': self.env.ref('my_module.sales_assistant').id
        })
        
        # Inicializar con el contexto del pedido
        context = {
            'customer_name': self.partner_id.name,
            'order_total': self.amount_total,
            'products': [line.product_id.name for line in self.order_line]
        }
        
        thread.message_post(
            body=f"AI Assistant ready to help with {self.name}",
            llm_role="system",
            body_json={'context': context}
        )
        
        return thread
```

### Integración con gestión de proyectos

```python
class ProjectTask(models.Model):
    _inherit = 'project.task'
    
    def get_ai_assistance(self, query):
        """Obtiene ayuda de la IA para las tareas de un proyecto"""
        assistant = self.env.ref('my_module.project_assistant')
        
        context = assistant.prepare_context(
            record=self,
            user_input=query
        )
        
        # Generar la respuesta de la IA con el contexto del proyecto
        response = assistant.generate_response(
            context=context,
            tools=['project_search', 'time_tracking', 'resource_planning']
        )
        
        return response
```

## Notas de migración

### Desde el módulo llm_prompt

**Migración automática** (versión 16.0.1.4.0):
- Todos los prompts existentes se migran automáticamente al módulo de asistentes
- La funcionalidad de plantillas queda integrada sin fricciones
- Se agregan capacidades de prueba mejoradas
- Sin pérdida de datos ni cambios de configuración

**Nuevas funciones:**
- Detección automática de argumentos para las plantillas existentes
- Asistente de pruebas mejorado con simulación de contexto
- Interfaz mejorada con gestión unificada de asistentes y prompts
- Mejor manejo de errores y validación

### Cambios incompatibles

Ninguno: es una actualización de consolidación con total compatibilidad hacia atrás.

## Especificaciones técnicas

### Información del módulo

- **Nombre**: LLM Assistant
- **Versión**: 16.0.1.4.0
- **Categoría**: Productivity
- **Licencia**: LGPL-3
- **Dependencias**: `serfe_llm`, `mail`
- **Autor**: Apexive Solutions LLC

### Modelos principales

- **`llm.assistant`**: configuración principal del asistente
- **`llm.prompt`**: gestión integrada de plantillas de prompts  
- **`llm.prompt.category`**: categorización de plantillas
- **`llm.assistant.test.wizard`**: pruebas y validación

## Rendimiento

- **Gestión inteligente del contexto**: recorte inteligente del historial de conversación
- **Caché de plantillas**: renderizado y detección de argumentos optimizados
- **Operaciones asíncronas**: pruebas y validación sin bloqueo
- **Optimización de base de datos**: almacenamiento eficiente de las configuraciones de asistentes

## Seguridad

- **Acceso por roles**: controla quién puede crear y modificar asistentes
- **Permisos de herramientas**: control granular del acceso a herramientas por asistente
- **Validación de plantillas**: evita la ejecución de plantillas maliciosas
- **Registro de auditoría**: seguimiento completo del uso y las modificaciones de los asistentes

## Módulos relacionados

- **`serfe_llm`**: infraestructura base y gestión de proveedores
- **`serfe_llm_thread`**: interfaces de chat y gestión de conversaciones
- **`serfe_llm_tool`**: function calling e integración con Odoo
- **`llm_generate`**: generación de contenido con integración de asistentes
- **`llm_knowledge`**: integración con RAG y base de conocimiento

## Soporte y recursos

- **Documentación**: [repositorio de GitHub](https://github.com/apexive/odoo-llm)
- **Guía de arquitectura**: [OVERVIEW.md](../OVERVIEW.md)
- **Ejemplos**: [ejemplos de asistentes](examples/)
- **Comunidad**: [GitHub Discussions](https://github.com/apexive/odoo-llm/discussions)

## Licencia

Este módulo está licenciado bajo [LGPL-3](https://www.gnu.org/licenses/lgpl-3.0.html).

---

*© 2025 Apexive Solutions LLC. Todos los derechos reservados.*
