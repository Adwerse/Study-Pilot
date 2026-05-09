#!/usr/bin/env sh
set -eu

POSTGRES_HOST="${POSTGRES_HOST:-postgres}"

psql_base() {
	psql -h "$POSTGRES_HOST" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -v ON_ERROR_STOP=1 "$@"
}

psql_base -c "CREATE TABLE IF NOT EXISTS schema_migrations (version text PRIMARY KEY, applied_at timestamptz NOT NULL DEFAULT now());"

for file in /migrations/*.sql; do
	if [ ! -e "$file" ]; then
		echo "No migrations found"
		exit 0
	fi

	version="$(basename "$file")"
	applied="$(psql_base -tAc "SELECT 1 FROM schema_migrations WHERE version = '$version'")"

	if [ "$applied" = "1" ]; then
		echo "Skipping $version"
		continue
	fi

	echo "Running $version"
	psql_base -f "$file"
	psql_base -c "INSERT INTO schema_migrations (version) VALUES ('$version');"
done
