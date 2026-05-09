#!/usr/bin/env sh
# Mints fresh production secrets for the NowGo Saúde backend.
# Output is plain text on stdout — pipe to your secret manager, do NOT commit.
set -eu

py() { python3 -c "$1"; }

echo "# NowGo Saúde production secrets."
echo "# DO NOT commit this output."
echo "# Pipe into GCP Secret Manager, e.g.:"
echo "#   ./scripts/generate-secrets.sh | while IFS='=' read -r k v; do"
echo "#     [ -z \"\$k\" ] || [[ \"\$k\" == \\#* ]] && continue"
echo "#     printf '%s' \"\$v\" | gcloud secrets create \"\$k\" --data-file=- \\"
echo "#       || printf '%s' \"\$v\" | gcloud secrets versions add \"\$k\" --data-file=-"
echo "#   done"
echo
echo "NOWGO_ADMIN_TOKEN=$(py 'import secrets; print(secrets.token_urlsafe(48))')"
echo "NOWGO_LGPD_OFFICER_TOKEN=$(py 'import secrets; print(secrets.token_urlsafe(48))')"
echo "NOWGO_PII_TOKEN_SECRET=$(py 'import secrets; print(secrets.token_urlsafe(64))')"
echo "NOWGO_PII_VAULT_KEY=$(py 'import os, base64; print(base64.b64encode(os.urandom(32)).decode())')"
echo "NOWGO_PII_VAULT_KEY_VERSION=1"
echo
echo "# WARNING: rotating NOWGO_PII_TOKEN_SECRET invalidates every previously"
echo "# stored anonymizer token. Only do it on a fresh database."
echo "# Rotating NOWGO_PII_VAULT_KEY requires bumping NOWGO_PII_VAULT_KEY_VERSION"
echo "# and keeping the old key resolvable by the vault service."
