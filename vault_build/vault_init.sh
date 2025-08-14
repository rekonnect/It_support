#!/bin/sh
set -e # Exit immediately if a command exits with a non-zero status.

# Define the log file path
LOG_FILE="/vault/logs/vault.log"

# Ensure the log directory and file exist and have correct permissions
mkdir -p /vault/logs
touch "$LOG_FILE"
chmod 600 "$LOG_FILE"

# Start Vault in the background, redirecting its output to the log file
echo "Starting Vault server... Logs will be available in the container at $LOG_FILE"
vault server -config=/etc/vault.d/vault.hcl > "$LOG_FILE" 2>&1 &
VAULT_PID=$!

# Give Vault a moment to start up or fail early
sleep 2

# Wait for Vault to become available
echo "Waiting for Vault to respond..."
VAULT_READY=false
for i in $(seq 1 30); do
    # First, check if the Vault process is still running.
    if ! kill -0 $VAULT_PID 2>/dev/null; then
        echo "Error: Vault process died unexpectedly!"
        echo "--- Dumping last 50 lines of log ---"
        tail -n 50 "$LOG_FILE"
        exit 1
    fi

    # Second, try to connect to the health endpoint.
    # We use '|| true' to prevent 'set -e' from exiting the script if curl fails to connect.
    status_code=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8200/v1/sys/health) || true

    if [ "$status_code" = "200" ] || [ "$status_code" = "501" ] || [ "$status_code" = "503" ]; then
        echo "Success: Vault is running and responsive. Status: $status_code"
        VAULT_READY=true
        break
    fi

    echo "Waiting for Vault... (attempt $i/30, status: $status_code)"
    sleep 1
done

# If Vault did not become ready, exit with an error and dump the logs.
if [ "$VAULT_READY" = "false" ]; then
    echo "Error: Vault failed to become ready in time."
    echo "--- Dumping last 50 lines of log ---"
    tail -n 50 "$LOG_FILE"
    exit 1
fi

# --- Initialize and Unseal ---
# This part only runs if Vault is responsive.

if [ ! -f "/vault/data/keys.json" ]; then
    echo "Initializing Vault for the first time..."
    vault operator init -key-shares=1 -key-threshold=1 -format=json > /vault/data/keys.json
fi

# Export the root token so 'vault' commands work
export VAULT_TOKEN=$(jq -r '.root_token' /vault/data/keys.json)
UNSEAL_KEY=$(jq -r '.unseal_keys_b64[0]' /vault/data/keys.json)

echo "Unsealing Vault..."
vault operator unseal "$UNSEAL_KEY" > /dev/null

# --- Configuration ---
echo "Applying post-unseal configuration..."

# Idempotently enable kv-v2 secrets engine at 'secret' path
vault secrets enable -path=secret kv-v2 > /dev/null 2>&1 || true

# Idempotently create a fixed token for API access
FIXED_TOKEN="myroottoken"
vault token create -id="$FIXED_TOKEN" -policy=root -renewable=true -period=72h > /dev/null 2>&1 || true
echo "API token 'myroottoken' ensured."

# Idempotently store the database secret
vault kv put secret/database url="postgresql://jules_user:jules_password@db:5432/jules_db" > /dev/null 2>&1
echo "Database secret ensured in Vault."

# --- Keep container alive ---
echo "Vault is ready and configured. Tailing logs to keep container alive..."
# Use tail -f on the log file and wait for the Vault process.
# This ensures that if either fails, the script will exit.
tail -f "$LOG_FILE" &
wait $VAULT_PID
