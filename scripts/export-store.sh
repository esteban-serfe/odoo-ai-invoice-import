#!/usr/bin/env bash
# Export the modules to publish in the Odoo Apps store into a directory, ready to
# be committed to a separate repository whose branch is named after the Odoo
# version (16.0). The store scans the repository root.
#
# llm, llm_tool and llm_training are not exported: Apexive already publishes them
# under those names, and the store resolves them as dependencies. This repository
# keeps them vendored so it stays self-contained for installs that do not use the
# store.
#
# Usage: scripts/export-store.sh <output-dir>
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="${1:?usage: $0 <output-dir>}"
MODULES=(
    serfe_llm_thread serfe_llm_assistant serfe_llm_litellm serfe_web_json_editor
    serfe_account_invoice_import_llm
    llm_litellm_responses llm_access_groups llm_invoice_ocr
)
# Dependencies that the store (or Odoo itself) must provide.
EXTERNAL="base web mail account llm llm_tool llm_training account_invoice_import"

mkdir -p "$OUT"
for m in "${MODULES[@]}"; do
    rm -rf "${OUT:?}/$m"
    # Skip compiled files and the test-only __pycache__
    rsync -a --exclude '__pycache__' --exclude '*.pyc' "$ROOT/$m" "$OUT/"
done
cp -r "$ROOT/LICENSES" "$ROOT/LICENSE" "$OUT/"
cat >"$OUT/README.md" <<README
# odoo-ai-addons (Odoo Apps store)

Modules published in the Odoo Apps store, exported from the main repository
(branch 16.0) with scripts/export-store.sh. Open issues and pull requests there.
README

# Every dependency must be exported or provided by the store: a missing one makes
# the store scan fail and unpublishes the whole repository.
python3 -I - "$OUT" "$EXTERNAL" "${MODULES[@]}" <<'PY'
import ast, os, sys
out, external, modules = sys.argv[1], set(sys.argv[2].split()), set(sys.argv[3:])
bad = []
for m in sorted(modules):
    manifest = ast.literal_eval(open(os.path.join(out, m, "__manifest__.py")).read())
    for dep in manifest.get("depends", []):
        if dep not in modules and dep not in external:
            bad.append(f"{m} depends on {dep}")
if bad:
    sys.exit("Unresolved dependencies:\n  " + "\n  ".join(bad))
print(f"OK: {len(modules)} modules, all dependencies resolved")
PY
