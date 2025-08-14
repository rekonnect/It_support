FROM ubuntu:22.04

# Install dependencies
RUN apt-get update && \
    apt-get install -y curl jq unzip && \
    rm -rf /var/lib/apt/lists/*

# Install Vault
RUN VAULT_VERSION=1.15.6 && \
    curl -fLO https://releases.hashicorp.com/vault/${VAULT_VERSION}/vault_${VAULT_VERSION}_linux_amd64.zip && \
    unzip vault_${VAULT_VERSION}_linux_amd64.zip -d /usr/local/bin && \
    rm vault_${VAULT_VERSION}_linux_amd64.zip && \
    chmod 0755 /usr/local/bin/vault

# Copy configuration and scripts
COPY vault.hcl /etc/vault.d/vault.hcl
COPY vault_init.sh /usr/local/bin/vault_init.sh
RUN chmod +x /usr/local/bin/vault_init.sh

# Create directories
RUN mkdir -p /vault/logs /vault/data

# Run the init script
CMD ["/usr/local/bin/vault_init.sh"]
