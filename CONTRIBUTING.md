# Contribuir

Español · [English](CONTRIBUTING.en.md)

1. Hacer un fork del repositorio y crear una rama desde `16.0`.
2. Hacer el cambio, usando [conventional commits](https://www.conventionalcommits.org/).
3. Ejecutar los tests y el lint (requiere Docker):

   ```
   scripts/run-tests.sh                      # todos los módulos
   scripts/run-tests.sh llm_invoice_ocr      # algunos módulos
   pre-commit run --all-files                # black, isort, flake8, pylint-odoo
   ```

   El script clona los repositorios de OCA en `.oca/`, construye una imagen de Odoo 16 (`scripts/Dockerfile`, o definí `ODOO_IMAGE`)
   y ejecuta los tests sobre una base limpia, en una red interna de Docker y sin credenciales de proveedor definidas.
   El lint cubre solo los módulos escritos en este repositorio; los vendorizados se excluyen para poder compararlos con upstream.
4. Abrir un pull request.
