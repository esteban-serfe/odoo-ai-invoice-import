# llm_access_groups

Español · [English](README.en.md)

Módulo de Odoo 16 que restringe quién puede usar las funciones de `odoo-llm`. No modifica esos módulos: los registros se parchean por ID externo.

## Para qué sirve
- Restringe los menús Configuración, Prompts y Training de LLM a *LLM Manager*. Los módulos upstream los dejan abiertos a todos los usuarios internos.
- Agrega el grupo *User: LLM Chatter*, necesario para usar el chat con IA (botón "AI" del chatter, menú Chat, `llm.thread`). La ACL de `llm.thread`, su regla de registro de hilos personales y el menú Chat pasan de *Internal User* a este grupo.
- Oculta el botón "AI" del chatter a los usuarios que no están en ese grupo.

## Requisitos / Dependencias
- Odoo 16 (Community)
- Módulos de Odoo: `serfe_llm_assistant`, `serfe_llm_thread`, `serfe_llm_training`

## Instalación
Agregar el addon al `addons_path` e instalarlo (Aplicaciones, o `-i llm_access_groups`).

## Configuración
Para que un usuario pueda chatear con el LLM, agregarlo a *User: LLM Chatter* (o a *LLM Manager*).

## Seguridad / Acceso
- **User: LLM Chatter** (`llm_access_groups.group_llm_chatter_user`) implica *Internal User*.
- **LLM Manager** (`serfe_llm.group_llm_manager`) implica *User: LLM Chatter* y conserva el acceso a los menús Configuración, Prompts y Training.
- Ocultar el botón del chatter es solo cosmético; la restricción real es la ACL de `llm.thread`.

## Multicompañía
Los grupos son globales, no por compañía.

## Licencia
LGPL-3
