# Módulo LLM Training

Español · [English](README.en.md)

Este módulo ofrece la funcionalidad para gestionar trabajos de fine-tuning de LLM en distintos proveedores. Permite crear, monitorear y administrar trabajos de fine-tuning directamente desde la interfaz de Odoo.

## Características

- Crear y gestionar trabajos de fine-tuning de LLM
- Seguimiento del estado y las métricas de los trabajos
- Soporte de múltiples proveedores de LLM (OpenAI, etc.)
- Integración con la gestión de datasets
- Monitoreo del estado de los trabajos y notificaciones

## Uso

### Acceder al módulo

1. Ir a **LLM > Training > Jobs** en el menú principal
2. Se muestra la lista de todos los trabajos de entrenamiento con su estado actual

### Crear un trabajo de entrenamiento

1. Hacer clic en el botón **Crear** de la lista de trabajos
2. Completar los campos obligatorios:
   - **Nombre**: un nombre descriptivo del trabajo
   - **Proveedor**: elegir el proveedor de LLM (por ejemplo, OpenAI)
   - **Modelo base**: elegir el modelo base a ajustar
   - **Datasets**: agregar uno o más datasets para el entrenamiento
3. Opcionalmente configurar:
   - **Descripción**: agregar detalles sobre el trabajo
   - **Hiperparámetros**: ajustar los parámetros de entrenamiento en formato JSON
4. Hacer clic en **Guardar** para crear el trabajo en estado borrador
5. Hacer clic en **Submit** para iniciar el entrenamiento

### Monitorear el estado del trabajo

1. El trabajo pasa por varios estados:

   - **Draft**: estado inicial
   - **Validating**: validando los datasets
   - **Preparing**: preparando los datos para el entrenamiento
   - **Queued**: el trabajo está en cola en el proveedor
   - **Training**: el entrenamiento está en curso
   - **Completed**: el entrenamiento terminó con éxito
   - **Failed**: el entrenamiento falló
   - **Cancelled**: el entrenamiento fue cancelado

2. Para los trabajos en curso, hacer clic en el botón **Check Status** para actualizar el estado

### Ver los resultados

1. Cuando un trabajo termina, ir a la pestaña **Results**
2. Ahí se encuentra:
   - El modelo ajustado resultante
   - Las métricas de entrenamiento
   - Los logs de entrenamiento

### Usar los modelos ajustados

Tras un entrenamiento exitoso, el modelo ajustado se agrega automáticamente a los modelos disponibles y puede usarse en:

- Hilos LLM
- Agentes LLM
- Cualquier otro componente que use modelos LLM

## Seguridad

El módulo sigue el modelo de seguridad estándar de dos niveles:

- Los usuarios comunes (base.group_user) tienen acceso de solo lectura
- Los LLM Managers (apx_llm.group_llm_manager) tienen acceso completo (CRUD)

## Información técnica

### Estructura de modelos

- `llm.training.job`: modelo principal de los trabajos de entrenamiento
- `llm.training.dataset`: modelo para gestionar los datasets de entrenamiento

### Integración con proveedores

El módulo usa una interfaz estandarizada para integrar proveedores:

- `start_training_job`: inicia el entrenamiento
- `check_training_job_status`: consulta el estado actual
- `cancel_training_job`: cancela un trabajo en curso

Los proveedores implementan estos métodos para manejar la lógica propia de cada uno.

## Resolución de problemas

### Problemas frecuentes

1. **Trabajo atascado en estado validating**:

   - Verificar que los datasets tengan el formato correcto
   - Verificar las credenciales del proveedor

2. **Trabajos fallidos**:

   - Revisar la pestaña Results para ver el detalle del error
   - Verificar que los hiperparámetros tengan el formato correcto

3. **Faltan modelos después de completar**:
   - Usar el botón Check Status para refrescar el estado del trabajo
   - Verificar el acceso del proveedor al modelo ajustado

## Contribuir

Seguí las guías estándar de desarrollo de Odoo al contribuir a este módulo.
