{
    "name": "Web JSON Editor (Serfe fork)",
    "version": "1.0",
    "category": "Web",
    "summary": "JSON Editor widget for Odoo",
    "description": """
        Provides a reusable JSON Editor widget for Odoo with schema-based autocomplete.
        Features:
        - JSON syntax highlighting
        - Schema-based autocomplete
        - Multiple view modes (code, tree, form, view)
        - Validation
    """,
    "depends": [
        "web",
    ],
    "assets": {
        "web.assets_backend": [
            # JSONEditor library
            "serfe_web_json_editor/static/lib/jsoneditor/jsoneditor.min.js",
            "serfe_web_json_editor/static/lib/jsoneditor/jsoneditor.min.css",
            "serfe_web_json_editor/static/lib/jsoneditor/img/jsoneditor-icons.svg",
            # Field widget
            "serfe_web_json_editor/static/src/fields/json_field.js",
            "serfe_web_json_editor/static/src/fields/json_field.xml",
            "serfe_web_json_editor/static/src/fields/json_field.scss",
            # OWL Component
            "serfe_web_json_editor/static/src/components/json_editor/json_editor.js",
            "serfe_web_json_editor/static/src/components/json_editor/json_editor.xml",
        ],
    },
    "author": "Apexive Solutions LLC, Serfe",
    "website": "https://github.com/apexive/odoo-llm",
    "installable": True,
    "application": False,
    "auto_install": False,
    "license": "LGPL-3",
}
