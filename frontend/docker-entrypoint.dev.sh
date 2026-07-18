#!/bin/sh
# Entrypoint do container de dev do frontend (Dockerfile.dev).
#
# nginx serve arquivo estático (./build), então "dev" aqui significa: builda
# uma vez pra `nginx` já ter o que servir no primeiro boot, sobe o `nginx` em
# foreground (processo principal do container) e, em paralelo, um watcher
# (nodemon) que re-builda sempre que `src/`/`public` mudam — sem precisar
# reiniciar o container a cada alteração de código.
set -e

echo "[dev-entrypoint] build inicial..."
npm run build

echo "[dev-entrypoint] iniciando watcher (rebuild em mudanças de src/public)..."
npx nodemon \
  --watch src \
  --watch public \
  --ext ts,tsx,js,jsx,scss,css,json,html \
  --exec "npm run build" &

echo "[dev-entrypoint] iniciando nginx..."
exec nginx -g "daemon off;"
