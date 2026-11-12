# Contributing

[Español](CONTRIBUTING.md) · English

1. Fork the repository and create a branch from `16.0`.
2. Make your change, using [conventional commits](https://www.conventionalcommits.org/).
3. Run the tests and the lint (Docker required):

   ```
   scripts/run-tests.sh                      # all modules
   scripts/run-tests.sh llm_invoice_ocr      # some modules
   pre-commit run --all-files                # black, isort, flake8, pylint-odoo
   ```

   The script clones the OCA repositories into `.oca/`, builds an Odoo 16 image (`scripts/Dockerfile`, or set `ODOO_IMAGE`)
   and runs the tests on a clean database, on an internal Docker network and without provider credentials set.
   Lint covers only the modules written in this repository; the vendored ones are excluded to stay diffable against upstream.
4. Open a pull request.
