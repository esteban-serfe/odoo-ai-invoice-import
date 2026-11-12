# Módulo LLM Thread

Español · [English](README.en.md)

Este módulo de Odoo ofrece la funcionalidad para gestionar e interactuar con hilos en el contexto de un modelo de lenguaje (LLM). Incluye componentes para hilos de chat, listas de mensajes y vistas de composición.

## Características

- **Gestión de hilos de chat**: crear, actualizar y administrar hilos de chat.
- **Lista de mensajes**: mostrar los mensajes de un hilo e interactuar con ellos.
- **Vista de composición**: escribir y enviar mensajes dentro de un hilo.
- **Integración de herramientas**: soporte de function calling y de herramientas que permiten a los modelos LLM realizar acciones en Odoo.

## Instalación

1. Clonar el repositorio en el directorio de addons de Odoo.
2. Instalar el módulo desde el menú Aplicaciones de Odoo.

## Uso

1. Primero, instalar y configurar al menos un módulo de proveedor LLM (por ejemplo, llm_openai, llm_anthropic, llm_ollama).
2. Configurar el proveedor con las API keys y ajustes correspondientes.
3. Ir al menú **LLM → Chat** de Odoo.
4. Hacer clic en "New Chat" para iniciar un hilo de conversación nuevo.
5. Se pueden crear varios hilos, ver los existentes e interactuar con los mensajes.
6. Si instalaste el módulo apx_llm_tool, podés habilitar el function calling, que permite a la IA realizar acciones en Odoo, como crear registros, buscar información o ejecutar lógica de negocio específica.

## Dependencias

- Odoo 16.0 o posterior
- Python 3.8 o posterior

## Contribuir

¡Las contribuciones son bienvenidas! Seguí las pautas de contribución del repositorio.

## Licencia

Este módulo está licenciado bajo la [Licencia MIT](https://opensource.org/licenses/MIT).
