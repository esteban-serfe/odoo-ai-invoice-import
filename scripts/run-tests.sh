#!/usr/bin/env bash
# Run the tests of this repo on a clean database, offline and without LITELLM_* set.
# Network is only used for the setup (cloning OCA repos, pulling/building images);
# the Odoo container runs on an internal Docker network.
#
# Usage: scripts/run-tests.sh [module,module,...]   (default: all modules)
# Env:   ODOO_IMAGE  use this image instead of building scripts/Dockerfile
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OCA_DIR="$ROOT/.oca"
NET="oai-test-net-$$"
PG="oai-test-pg-$$"

ALL_MODULES=$(cd "$ROOT" && ls -d */ | tr -d / | while read -r d; do
    [ -f "$d/__manifest__.py" ] && echo "$d"
done | paste -sd,)
MODULES="${1:-$ALL_MODULES}"
TAGS=$(echo "$MODULES" | sed 's#\([^,]*\)#/\1#g')

# OCA dependencies from oca_dependencies.txt ("name url branch")
ADDONS_PATH="/usr/lib/python3/dist-packages/odoo/addons,/mnt/repo"
MOUNTS=(-v "$ROOT:/mnt/repo:ro")
mkdir -p "$OCA_DIR"
while read -r name url branch; do
    case "$name" in "" | \#*) continue ;; esac
    [ -d "$OCA_DIR/$name" ] || git clone -q --depth 1 -b "$branch" "$url" "$OCA_DIR/$name"
    MOUNTS+=(-v "$OCA_DIR/$name:/mnt/$name:ro")
    ADDONS_PATH="$ADDONS_PATH,/mnt/$name"
done <"$ROOT/oca_dependencies.txt"

if [ -z "${ODOO_IMAGE:-}" ]; then
    ODOO_IMAGE=oai-odoo-test:16
    docker build -q -t "$ODOO_IMAGE" -f "$ROOT/scripts/Dockerfile" "$ROOT" >/dev/null
fi

cleanup() {
    docker stop "$PG" >/dev/null 2>&1 || true
    docker network rm "$NET" >/dev/null 2>&1 || true
}
trap cleanup EXIT

docker network create --internal "$NET" >/dev/null
docker run -d --rm --name "$PG" --network "$NET" --tmpfs /var/lib/postgresql/data \
    -e POSTGRES_USER=odoo -e POSTGRES_PASSWORD=odoo -e POSTGRES_DB=postgres \
    postgres:15 >/dev/null
until docker exec "$PG" pg_isready -q; do sleep 1; done

docker run --rm --network "$NET" -u odoo --entrypoint odoo "${MOUNTS[@]}" "$ODOO_IMAGE" \
    -c /dev/null -d oai_test --db_host "$PG" --db_user odoo --db_password odoo \
    --addons-path="$ADDONS_PATH" -i "$MODULES" --test-tags "$TAGS" \
    --stop-after-init --log-level=test
