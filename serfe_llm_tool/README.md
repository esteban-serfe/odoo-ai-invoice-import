# Herramientas LLM para Odoo

Español · [English](README.en.md)

Framework mejorado de function calling con almacenamiento de datos estructurados, manejo de errores completo e integración con MCP. Este módulo permite a los LLM interactuar con los datos de Odoo y ejecutar acciones a través de un sistema de herramientas potente y seguro.

## Descripción general

El módulo LLM Tool es la base del function calling con IA en Odoo: permite a los LLM interactuar con datos de negocio, ejecutar acciones y realizar operaciones complejas. Con la versión 16.0.3.0.0, el módulo incorpora una refactorización importante con almacenamiento de datos estructurados en `body_json` y capacidades de ejecución mejoradas.

### Capacidades principales

- **Framework de function calling** - Permite a los LLM ejecutar métodos y acciones de Odoo
- **Almacenamiento de datos estructurados** - Los resultados de las herramientas se guardan en formato `body_json` para una mejor organización
- **Integración con MCP** - Compatibilidad con Model Context Protocol para definiciones de herramientas estandarizadas  
- **Marco de seguridad** - Sistema de consentimiento del usuario y control de acceso por permisos
- **Manejo de errores** - Propagación de errores y mecanismos de recuperación completos
- **Generación de esquemas** - Detección automática del esquema de entrada a partir de la firma de los métodos

## Características clave

### Sistema de herramientas mejorado (versión 16.0.3.0.0)

**Formato de mensaje estructurado:**

```python
# Nuevo formato body_json para los mensajes de herramientas
thread.message_post(
    body_json={
        "tool_call_id": "call_abc123",
        "function": "search_records",
        "arguments": {
            "model": "sale.order",
            "domain": [['state', '=', 'draft']],
            "limit": 10
        },
        "result": {
            "records": [...],
            "count": 5,
            "execution_time": 0.045
        },
        "status": "success"
    },
    llm_role="tool"
)
```

**Ventajas del nuevo formato:**
- **Mejor organización**: todos los datos de la herramienta en formato JSON estructurado
- **Depuración mejorada**: separación clara de entrada, salida y metadatos
- **Mejor analítica**: análisis sencillo de los patrones de uso de las herramientas
- **Compatibilidad con MCP**: formato estándar para el seguimiento de llamadas a herramientas

### Tipos de implementación de herramientas

#### 1. Herramientas de acción de servidor
Ejecutan acciones de servidor existentes de Odoo:
```python
class LLMToolServerAction(models.Model):
    _name = "llm.tool.server.action"
    _inherit = "llm.tool"
    
    server_action_id = fields.Many2one('ir.actions.server', required=True)
    
    def server_action_execute(self, **kwargs):
        """Ejecuta la acción de servidor con parámetros"""
        return self.server_action_id.with_context(**kwargs).run()
```

#### 2. Herramientas de llamada a método  
Llaman a métodos específicos de un modelo:
```python
class LLMToolMethodCall(models.Model):
    _name = "llm.tool.method.call"
    _inherit = "llm.tool"
    
    target_model = fields.Char(required=True)
    target_method = fields.Char(required=True)
    
    def method_call_execute(self, record_ids=None, **kwargs):
        """Ejecuta el método sobre los registros de destino"""
        Model = self.env[self.target_model]
        records = Model.browse(record_ids) if record_ids else Model
        method = getattr(records, self.target_method)
        return method(**kwargs)
```

#### 3. Herramientas de búsqueda
Buscan y recuperan registros de Odoo:
```python
class LLMToolSearch(models.Model):
    _name = "llm.tool.search"
    _inherit = "llm.tool"
    
    def search_execute(self, model, domain=None, fields=None, limit=10, **kwargs):
        """Busca registros con un dominio y devuelve los campos indicados"""
        Model = self.env[model]
        domain = domain or []
        
        records = Model.search(domain, limit=limit)
        
        if fields:
            return records.read(fields)
        else:
            return [{
                'id': rec.id,
                'name': rec.display_name,
                'model': model
            } for rec in records]
```

#### 4. Herramientas de función personalizada
Ejecutan funciones de Python personalizadas:
```python
class LLMToolCustomFunction(models.Model):
    _name = "llm.tool.custom.function"
    _inherit = "llm.tool"
    
    function_code = fields.Text(required=True)
    
    def custom_function_execute(self, **kwargs):
        """Ejecuta código Python personalizado de forma segura"""
        # Entorno de ejecución seguro
        safe_globals = {
            'env': self.env,
            'fields': fields,
            'models': models,
            '_': _,
            '__builtins__': {}  # Builtins restringidos
        }
        
        exec(self.function_code, safe_globals, kwargs)
        return kwargs.get('result', 'Function executed successfully')
```

### Generación automática de esquemas

**A partir de la firma de los métodos:**
```python
def get_input_schema_from_method(self):
    """Genera el esquema JSON a partir de la firma del método"""
    import inspect
    
    if self.implementation == 'search':
        method = self.search_execute
    elif self.implementation == 'method_call':
        method = self.method_call_execute
    else:
        return {}
    
    signature = inspect.signature(method)
    schema = {"type": "object", "properties": {}}
    
    for param_name, param in signature.parameters.items():
        if param_name in ['self', 'kwargs']:
            continue
            
        prop = {"type": "string"}  # Tipo por defecto
        
        # Detección por type hints
        if param.annotation != inspect.Parameter.empty:
            if param.annotation == int:
                prop["type"] = "integer"
            elif param.annotation == bool:
                prop["type"] = "boolean"
            elif param.annotation == list:
                prop["type"] = "array"
        
        # Valor por defecto
        if param.default != inspect.Parameter.empty:
            prop["default"] = param.default
        
        schema["properties"][param_name] = prop
    
    return schema
```

**Definición manual del esquema:**
```python
# Esquema JSON personalizado para herramientas complejas
tool_schema = {
    "type": "object",
    "properties": {
        "query": {
            "type": "string",
            "description": "Search query string",
            "minLength": 1
        },
        "filters": {
            "type": "object",
            "properties": {
                "date_from": {"type": "string", "format": "date"},
                "date_to": {"type": "string", "format": "date"},
                "status": {
                    "type": "string", 
                    "enum": ["draft", "confirmed", "done"]
                }
            }
        },
        "limit": {
            "type": "integer",
            "minimum": 1,
            "maximum": 100,
            "default": 10
        }
    },
    "required": ["query"]
}
```

## Marco de seguridad

### Sistema de consentimiento del usuario

```python
class LLMTool(models.Model):
    _inherit = "llm.tool"
    
    requires_user_consent = fields.Boolean(
        default=False,
        help="Require user confirmation before execution"
    )
    
    destructive_hint = fields.Boolean(
        default=False, 
        help="Tool may modify or delete data"
    )
    
    read_only_hint = fields.Boolean(
        default=True,
        help="Tool only reads data without modifications"
    )
    
    def execute_with_consent(self, user_id, **kwargs):
        """Ejecuta la herramienta validando el consentimiento del usuario"""
        if self.requires_user_consent:
            consent = self._check_user_consent(user_id, **kwargs)
            if not consent:
                raise UserError("User consent required for this operation")
        
        return self.execute(**kwargs)
```

### Marco de permisos

```python
def check_execution_permissions(self, user_id=None):
    """Verifica si el usuario tiene permiso para ejecutar esta herramienta"""
    user = self.env['res.users'].browse(user_id) if user_id else self.env.user
    
    # Verificar el acceso básico a la herramienta
    if not user.has_group('serfe_llm.group_llm_user'):
        return False, "User not in LLM User group"
    
    # Verificar los permisos propios de la herramienta
    if self.destructive_hint and not user.has_group('serfe_llm.group_llm_manager'):
        return False, "Destructive operations require LLM Manager role"
    
    # Verificar los permisos sobre el modelo
    if hasattr(self, 'target_model'):
        Model = self.env[self.target_model]
        if not Model.check_access_rights('read', raise_exception=False):
            return False, f"No read access to {self.target_model}"
    
    return True, "Permission granted"
```

## Ejemplos de ejecución de herramientas

### Herramientas de CRM

```python
class CRMSearchTool(models.Model):
    _name = "llm.tool.crm.search"
    _inherit = "llm.tool"
    
    def crm_search_execute(self, query=None, stage=None, user_id=None, limit=10):
        """Busca oportunidades del CRM con filtrado inteligente"""
        domain = []
        
        if query:
            domain.extend([
                '|', '|',
                ('name', 'ilike', query),
                ('partner_id.name', 'ilike', query),
                ('description', 'ilike', query)
            ])
        
        if stage:
            domain.append(('stage_id.name', 'ilike', stage))
            
        if user_id:
            domain.append(('user_id', '=', user_id))
        
        opportunities = self.env['crm.lead'].search(domain, limit=limit)
        
        return {
            'count': len(opportunities),
            'opportunities': [{
                'id': opp.id,
                'name': opp.name,
                'partner': opp.partner_id.name,
                'stage': opp.stage_id.name,
                'expected_revenue': opp.expected_revenue,
                'probability': opp.probability,
                'date_deadline': opp.date_deadline.isoformat() if opp.date_deadline else None
            } for opp in opportunities]
        }
```

### Herramientas de inventario

```python
class InventoryTool(models.Model):
    _name = "llm.tool.inventory"
    _inherit = "llm.tool"
    
    def inventory_check_execute(self, product_ids=None, location_id=None):
        """Consulta los niveles de inventario de los productos"""
        domain = []
        
        if product_ids:
            domain.append(('product_id', 'in', product_ids))
        if location_id:
            domain.append(('location_id', '=', location_id))
        
        quants = self.env['stock.quant'].search(domain)
        
        inventory_data = {}
        for quant in quants:
            product_id = quant.product_id.id
            if product_id not in inventory_data:
                inventory_data[product_id] = {
                    'product_name': quant.product_id.name,
                    'total_quantity': 0,
                    'locations': []
                }
            
            inventory_data[product_id]['total_quantity'] += quant.quantity
            inventory_data[product_id]['locations'].append({
                'location': quant.location_id.name,
                'quantity': quant.quantity,
                'reserved_quantity': quant.reserved_quantity
            })
        
        return inventory_data
```

### Herramientas de generación de reportes

```python
class ReportGenerationTool(models.Model):
    _name = "llm.tool.report.generation"
    _inherit = "llm.tool"
    
    def report_generate_execute(self, report_name, record_ids, format='pdf'):
        """Genera reportes para los registros indicados"""
        report = self.env['ir.actions.report']._get_report_from_name(report_name)
        if not report:
            raise UserError(f"Report '{report_name}' not found")
        
        records = self.env[report.model].browse(record_ids)
        
        if format.lower() == 'pdf':
            pdf_content, _ = report._render_qweb_pdf(records.ids)
            return {
                'format': 'pdf',
                'content': base64.b64encode(pdf_content).decode(),
                'filename': f"{report_name}_{len(record_ids)}_records.pdf"
            }
        elif format.lower() == 'html':
            html_content, _ = report._render_qweb_html(records.ids)
            return {
                'format': 'html',
                'content': html_content,
                'filename': f"{report_name}_{len(record_ids)}_records.html"
            }
        else:
            raise UserError(f"Unsupported format: {format}")
```

## Integración con MCP

### Definición de herramientas para MCP

```python
def get_mcp_tool_definition(self):
    """Genera una definición de herramienta compatible con MCP"""
    return {
        "name": self.name,
        "description": self.description,
        "inputSchema": {
            "type": "object",
            "properties": json.loads(self.input_schema or '{}').get('properties', {}),
            "required": json.loads(self.input_schema or '{}').get('required', [])
        }
    }

def execute_mcp_call(self, arguments):
    """Ejecuta una llamada a herramienta proveniente de un cliente MCP"""
    try:
        result = self.execute(**arguments)
        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(result, default=str, indent=2)
                }
            ]
        }
    except Exception as e:
        return {
            "content": [
                {
                    "type": "text", 
                    "text": f"Error executing tool: {str(e)}"
                }
            ],
            "isError": True
        }
```

### Integración con un servidor MCP

```python
class MCPToolServer(models.Model):
    _name = "llm.mcp.tool.server"
    _inherit = "llm.mcp.server"
    
    def get_available_tools(self):
        """Devuelve todas las herramientas disponibles para los clientes MCP"""
        tools = self.env['llm.tool'].search([('active', '=', True)])
        return [tool.get_mcp_tool_definition() for tool in tools]
    
    def call_tool(self, name, arguments):
        """Atiende una llamada a herramienta de un cliente MCP"""
        tool = self.env['llm.tool'].search([('name', '=', name)], limit=1)
        if not tool:
            raise UserError(f"Tool '{name}' not found")
        
        return tool.execute_mcp_call(arguments)
```

## Manejo de errores y registro

### Gestión de errores completa

```python
def execute_with_error_handling(self, **kwargs):
    """Ejecuta la herramienta con manejo de errores completo"""
    execution_start = time.time()
    
    try:
        # Validar las entradas
        self._validate_execution_inputs(**kwargs)
        
        # Verificar los permisos
        can_execute, error_msg = self.check_execution_permissions()
        if not can_execute:
            raise PermissionError(error_msg)
        
        # Ejecutar la herramienta
        result = self.execute(**kwargs)
        
        # Registrar la ejecución exitosa
        self._log_tool_execution(
            status='success',
            duration=time.time() - execution_start,
            result_size=len(str(result))
        )
        
        return result
        
    except ValidationError as e:
        self._log_tool_execution(
            status='validation_error',
            error=str(e),
            duration=time.time() - execution_start
        )
        raise
        
    except PermissionError as e:
        self._log_tool_execution(
            status='permission_error', 
            error=str(e),
            duration=time.time() - execution_start
        )
        raise
        
    except Exception as e:
        self._log_tool_execution(
            status='execution_error',
            error=str(e),
            duration=time.time() - execution_start
        )
        raise UserError(f"Tool execution failed: {str(e)}")
```

### Registro de ejecuciones

```python
def _log_tool_execution(self, status, duration=None, error=None, result_size=None):
    """Registra la ejecución de la herramienta para monitoreo y depuración"""
    log_data = {
        'tool_id': self.id,
        'tool_name': self.name,
        'user_id': self.env.uid,
        'status': status,
        'timestamp': fields.Datetime.now(),
        'duration': duration,
        'error_message': error,
        'result_size_bytes': result_size
    }
    
    # Crear el registro de ejecución
    self.env['llm.tool.execution.log'].create(log_data)
    
    # Registrar también en el log del sistema para monitoreo
    if status == 'success':
        _logger.info(f"Tool '{self.name}' executed successfully in {duration:.3f}s")
    else:
        _logger.warning(f"Tool '{self.name}' failed: {error}")
```

## Referencia de la API

### Métodos principales

```python
# Ejecutar la herramienta con argumentos
def execute(self, **kwargs):
    """Método de ejecución principal - lo implementan las subclases"""

# Obtener la definición de la herramienta para los modelos de IA
def get_tool_definition(self):
    """Devuelve la definición en formato function calling de OpenAI"""

# Validar los permisos de ejecución
def check_execution_permissions(self, user_id=None):
    """Verifica si el usuario puede ejecutar esta herramienta"""

# Generar el esquema de entrada
def get_input_schema(self):
    """Devuelve el esquema JSON de las entradas de la herramienta"""

# Integración con MCP
def get_mcp_tool_definition(self):
    """Devuelve una definición de herramienta compatible con MCP"""
```

### Registro de herramientas

```python
@api.model
def _get_available_implementations(self):
    """Devuelve los tipos de implementación de herramienta disponibles"""
    return [
        ('search', 'Search Records'),
        ('server_action', 'Server Action'),
        ('method_call', 'Method Call'),
        ('custom_function', 'Custom Function')
    ]
```

## Optimizaciones de rendimiento

### Caché de ejecución

```python
@api.model
@tools.ormcache('tool_id', 'cache_key')
def _get_cached_execution_result(self, tool_id, cache_key):
    """Cachea los resultados de ejecución de las operaciones de solo lectura"""
    return self._execute_without_cache()

def execute_with_cache(self, **kwargs):
    """Ejecuta con caché de resultados para herramientas de solo lectura"""
    if not self.read_only_hint:
        return self.execute(**kwargs)
    
    cache_key = self._generate_cache_key(**kwargs)
    return self._get_cached_execution_result(self.id, cache_key)
```

### Operaciones por lotes

```python
def execute_batch(self, operation_list):
    """Ejecuta varias operaciones de la herramienta por lotes"""
    results = []
    
    # Agrupar las operaciones por tipo para optimizar
    grouped_ops = self._group_operations_by_type(operation_list)
    
    for op_type, operations in grouped_ops.items():
        if op_type == 'search':
            # Búsquedas por lotes
            batch_results = self._execute_batch_search(operations)
        elif op_type == 'method_call':
            # Llamadas a método por lotes
            batch_results = self._execute_batch_method_calls(operations)
        else:
            # Ejecutar individualmente
            batch_results = [self.execute(**op) for op in operations]
        
        results.extend(batch_results)
    
    return results
```

## Notas de migración

### Cambios de la versión 16.0.3.0.0

**Refactorización importante:**
- El **formato de los mensajes de herramientas** pasó al formato estructurado `body_json`
- **Ejecución mejorada** con mejor manejo de errores y registro
- **Integración con MCP** para definiciones de herramientas estandarizadas
- **Mejoras de seguridad** con un marco de permisos reforzado

**Script de migración:** convierte automáticamente los mensajes de herramientas existentes:
```python
def migrate_tool_messages(env):
    """Convierte los mensajes de herramientas viejos al nuevo formato body_json"""
    tool_messages = env['mail.message'].search([
        ('llm_role', '=', 'tool'),
        ('body_json', '=', False)
    ])
    
    for message in tool_messages:
        # Extraer los datos de la herramienta del formato anterior
        old_data = message._extract_legacy_tool_data()
        
        # Convertir al nuevo formato
        new_format = {
            "tool_call_id": old_data.get('call_id'),
            "function": old_data.get('function_name'),
            "arguments": old_data.get('arguments', {}),
            "result": old_data.get('result'),
            "status": "success" if old_data.get('result') else "error"
        }
        
        message.body_json = new_format
```

**Cambios incompatibles:** ninguno para los usuarios finales; solo cambia el formato interno de los mensajes

## Especificaciones técnicas

### Información del módulo

- **Nombre**: LLM Tool
- **Versión**: 16.0.3.0.0
- **Categoría**: Technical
- **Licencia**: LGPL-3
- **Dependencias**: `serfe_llm`, `mail`
- **Autor**: Apexive Solutions LLC

### Modelos principales

- **`llm.tool`**: framework base de herramientas
- **`llm.tool.execution.log`**: registro y monitoreo de ejecuciones
- **Modelos de implementación**: varios tipos de herramientas especializadas

### Funciones de seguridad

- Sistema de consentimiento del usuario para operaciones sensibles
- Control de acceso basado en permisos
- Registro de ejecuciones y pistas de auditoría
- Entornos de ejecución seguros para el código personalizado

## Módulos relacionados

- **`serfe_llm`**: infraestructura base y sistema de mensajería
- **`llm_assistant`**: configuración de asistentes con selección de herramientas
- **`llm_thread`**: interfaz de chat con visualización de la ejecución de herramientas
- **`llm_tool_knowledge`**: herramienta de búsqueda en la base de conocimiento
- **`llm_mcp`**: implementación del servidor Model Context Protocol

## Soporte y recursos

- **Documentación**: [repositorio de GitHub](https://github.com/apexive/odoo-llm)
- **Guía de arquitectura**: [OVERVIEW.md](../OVERVIEW.md)
- **Ejemplos de herramientas**: [guía de desarrollo de herramientas](examples/)
- **Comunidad**: [GitHub Discussions](https://github.com/apexive/odoo-llm/discussions)

## Licencia

Este módulo está licenciado bajo [LGPL-3](https://www.gnu.org/licenses/lgpl-3.0.html).

---

*© 2025 Apexive Solutions LLC. Todos los derechos reservados.*
