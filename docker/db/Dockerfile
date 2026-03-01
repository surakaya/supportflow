FROM mysql:8.0

COPY db/schema.sql /docker-entrypoint-initdb.d/01-schema.sql
COPY db/init/init.sql /docker-entrypoint-initdb.d/02-init.sql
