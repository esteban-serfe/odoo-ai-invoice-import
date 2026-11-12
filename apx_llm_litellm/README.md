# Integración del proxy LiteLLM para Odoo

Español · [English](README.en.md)

Este módulo integra el proxy LiteLLM con el framework LLM de Odoo, dando acceso a múltiples proveedores de LLM a través de un único proxy.

## Características

- Conexión al proxy LiteLLM con autenticación adecuada
- Soporte de múltiples proveedores de LLM a través de un único endpoint
- Generación de texto
- Descubrimiento automático de modelos
- Límites de uso y seguimiento de costos a través del proxy

## Configuración

1. Instalar el módulo
2. Ir a **LLM > Configuración > Proveedores**
3. Crear un proveedor nuevo y elegir "LiteLLM" como tipo de proveedor
4. Ingresar la URL de tu proxy LiteLLM y la API key (si hace falta)
5. Hacer clic en "Fetch Models" para importar los modelos disponibles

## Estado actual

Este módulo está en una etapa temprana de desarrollo. Está implementada la funcionalidad básica para conectarse al proxy LiteLLM y generar texto, pero las funciones avanzadas siguen en desarrollo.

## Detalles técnicos

Este módulo extiende el framework base de integración LLM con implementaciones específicas de LiteLLM:

- Implementa el cliente del proxy LiteLLM con autenticación adecuada
- Mapea los formatos de LiteLLM a los formatos LLM de Odoo
- Maneja los casos de error básicos

## Dependencias

- llm (LLM Integration Base)

## Licencia

LGPL-3
