#!/usr/bin/env bash
set -euo pipefail

NAME="${1:-}"
TITLE="${2:-$NAME}"

# --- Validate input ---
if [ -z "$NAME" ]; then
    printf '{"ok":false,"message":"Usage: create.sh <site-name> [site-title]"}\n'
    exit 1
fi

if ! echo "$NAME" | grep -qE '^[a-z0-9]([a-z0-9-]*[a-z0-9])?$'; then
    printf '{"ok":false,"message":"Site name must be lowercase alphanumeric with optional hyphens (e.g. my-demo). No leading/trailing hyphens."}\n'
    exit 1
fi

SITES_DIR="$HOME/wordpress-sites"
SITE_DIR="$SITES_DIR/$NAME"

if [ -d "$SITE_DIR" ]; then
    printf '{"ok":false,"name":"%s","message":"Site already exists at %s"}\n' "$NAME" "$SITE_DIR"
    exit 1
fi

# --- Find a free port starting at 8080 ---
find_free_port() {
    local port=8080
    while lsof -i ":$port" &>/dev/null 2>&1; do
        port=$((port + 1))
    done
    echo "$port"
}

PORT=$(find_free_port)
echo "Using port $PORT" >&2

# --- Generate passwords ---
DB_ROOT_PASS=$(openssl rand -base64 16 | tr -d '=/+')
DB_PASS=$(openssl rand -base64 16 | tr -d '=/+')
ADMIN_PASS=$(openssl rand -base64 16 | tr -d '=/+')
ADMIN_USER="admin"
ADMIN_EMAIL="admin@example.local"

# --- Create site directory ---
mkdir -p "$SITE_DIR"

# --- Write .env (chmod 600 — contains all secrets) ---
cat > "$SITE_DIR/.env" <<EOF
SITE_NAME=$NAME
WP_PORT=$PORT
DB_ROOT_PASSWORD=$DB_ROOT_PASS
DB_PASSWORD=$DB_PASS
WP_ADMIN_USER=$ADMIN_USER
WP_ADMIN_PASS=$ADMIN_PASS
WP_ADMIN_EMAIL=$ADMIN_EMAIL
EOF
chmod 600 "$SITE_DIR/.env"

# --- Write docker-compose.yml ---
# Note: single-quoted heredoc delimiter prevents variable expansion inside the yaml
cat > "$SITE_DIR/docker-compose.yml" <<'COMPOSE_EOF'
services:
  db:
    image: mysql:8.0
    restart: unless-stopped
    environment:
      MYSQL_ROOT_PASSWORD: ${DB_ROOT_PASSWORD}
      MYSQL_DATABASE: wordpress
      MYSQL_USER: wordpress
      MYSQL_PASSWORD: ${DB_PASSWORD}
    volumes:
      - db_data:/var/lib/mysql
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost", "-uroot", "-p${DB_ROOT_PASSWORD}"]
      interval: 10s
      timeout: 5s
      retries: 12
      start_period: 30s

  wordpress:
    image: wordpress:latest
    restart: unless-stopped
    depends_on:
      db:
        condition: service_healthy
    ports:
      - "${WP_PORT}:80"
    environment:
      WORDPRESS_DB_HOST: db
      WORDPRESS_DB_NAME: wordpress
      WORDPRESS_DB_USER: wordpress
      WORDPRESS_DB_PASSWORD: ${DB_PASSWORD}
      WORDPRESS_TABLE_PREFIX: wp_
    volumes:
      - wp_data:/var/www/html
    healthcheck:
      test: ["CMD-SHELL", "curl -s http://localhost/ -o /dev/null -w '%{http_code}' | grep -qE '^[23]' || exit 1"]
      interval: 15s
      timeout: 10s
      retries: 12
      start_period: 60s

volumes:
  db_data:
  wp_data:
COMPOSE_EOF

# --- Start containers ---
echo "Starting containers..." >&2
cd "$SITE_DIR"
docker compose --project-name "$NAME" up -d >&2

# --- Wait for WordPress container to be healthy ---
echo "Waiting for WordPress to be ready (this typically takes 1-2 minutes)..." >&2
CONTAINER="${NAME}-wordpress-1"
TIMEOUT=240
ELAPSED=0

while true; do
    STATUS=$(docker inspect --format='{{.State.Health.Status}}' "$CONTAINER" 2>/dev/null || echo "starting")
    if [ "$STATUS" = "healthy" ]; then
        echo "WordPress is healthy" >&2
        break
    fi
    if [ "$ELAPSED" -ge "$TIMEOUT" ]; then
        printf '{"ok":false,"name":"%s","message":"Timed out waiting for WordPress after %ds. Check: docker logs %s"}\n' \
            "$NAME" "$TIMEOUT" "$CONTAINER"
        exit 1
    fi
    echo "  Status: $STATUS (${ELAPSED}s elapsed)" >&2
    sleep 5
    ELAPSED=$((ELAPSED + 5))
done

# --- Install WP-CLI into the WordPress container ---
echo "Installing WP-CLI..." >&2
docker exec "$CONTAINER" bash -c \
    "curl -sL https://raw.githubusercontent.com/wp-cli/builds/gh-pages/phar/wp-cli.phar -o /usr/local/bin/wp \
     && chmod +x /usr/local/bin/wp" >&2

# --- Run wp core install via WP-CLI ---
echo "Configuring WordPress via WP-CLI..." >&2
docker exec --user www-data "$CONTAINER" wp core install \
    --url="http://localhost:${PORT}" \
    --title="$TITLE" \
    --admin_user="$ADMIN_USER" \
    --admin_password="$ADMIN_PASS" \
    --admin_email="$ADMIN_EMAIL" \
    --skip-email >&2

# --- Force password change on first login ---
docker exec --user www-data "$CONTAINER" wp user meta update 1 default_password_nag 1 >&2

# --- Output result ---
printf '{"ok":true,"name":"%s","url":"http://localhost:%s","admin_url":"http://localhost:%s/wp-admin","admin_user":"%s","admin_password":"%s","message":"WordPress site ready. You will be prompted to change your password on first login."}\n' \
    "$NAME" "$PORT" "$PORT" "$ADMIN_USER" "$ADMIN_PASS"
