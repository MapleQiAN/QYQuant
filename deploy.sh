#!/usr/bin/env bash

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_info() {
  echo -e "${GREEN}[INFO]${NC} $1"
}

print_warn() {
  echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
  echo -e "${RED}[ERROR]${NC} $1"
}

check_docker() {
  if ! command -v docker >/dev/null 2>&1; then
    print_error "Docker is not installed."
    exit 1
  fi

  if ! docker compose version >/dev/null 2>&1; then
    print_error "Docker Compose v2 is required."
    exit 1
  fi
}

ensure_env() {
  if [[ ! -f .env ]]; then
    cp .env.example .env
    print_warn ".env did not exist. A default one has been created from .env.example."
    print_warn "Review SECRET_KEY, JWT_SECRET, FERNET_KEY, CORS_ORIGINS and exposed ports before production use."
  fi
}

parse_args() {
  REBUILD=false

  while [[ $# -gt 0 ]]; do
    case "$1" in
      --rebuild|--build|-b)
        REBUILD=true
        shift
        ;;
      --help|-h)
        cat <<'EOF'
Usage: ./deploy.sh [--rebuild]

  --rebuild, --build, -b    Rebuild images before starting services
EOF
        exit 0
        ;;
      *)
        print_error "Unknown argument: $1"
        exit 1
        ;;
    esac
  done
}

start_stack() {
  if [[ "${REBUILD}" == "true" ]]; then
    print_info "Rebuilding images and starting the QYQuant Docker stack..."
    docker compose up -d --build
  else
    print_info "Starting the QYQuant Docker stack with existing images..."
    docker compose up -d
  fi
  print_info "Services started."
}

show_access_info() {
  frontend_port=$(grep -E '^FRONTEND_PORT=' .env | cut -d '=' -f2 || true)
  backend_port=$(grep -E '^BACKEND_PORT=' .env | cut -d '=' -f2 || true)
  frontend_port=${frontend_port:-58888}
  backend_port=${backend_port:-59999}

  echo
  print_info "Frontend: http://localhost:${frontend_port}"
  print_info "Backend API: http://localhost:${backend_port}"
  print_info "Swagger UI: http://localhost:${backend_port}/api/docs"
  echo
  print_info "Useful commands:"
  echo "  docker compose ps"
  echo "  docker compose logs -f backend"
  echo "  docker compose logs -f frontend"
  echo "  docker compose down"
}

main() {
  parse_args "$@"
  check_docker
  ensure_env
  start_stack
  show_access_info
}

main "$@"
