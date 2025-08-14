#!/bin/sh

# Get Vault status with timeout
response=$(curl -s -m 5 -o /dev/null -w "%{http_code}" "http://127.0.0.1:8200/v1/sys/health" 2>/dev/null)

# Accept all valid Vault status codes
case "$response" in
    200|429|473|501|503)
        exit 0
        ;;
    *)
        echo "Unexpected status: $response"
        exit 1
        ;;
esac
