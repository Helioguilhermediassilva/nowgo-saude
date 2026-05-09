#!/usr/bin/env bash
# Manual deploy helper for the NowGo Saúde backend on Cloud Run + Cloud SQL.
#
# Prereqs (run once per project):
#   gcloud auth login
#   gcloud config set project "$GCP_PROJECT"
#   gcloud services enable run.googleapis.com sqladmin.googleapis.com \
#       artifactregistry.googleapis.com cloudbuild.googleapis.com \
#       secretmanager.googleapis.com
#   gcloud artifacts repositories create "$AR_REPO" \
#       --repository-format=docker --location="$REGION"
#   gcloud sql instances create "$SQL_INSTANCE_NAME" \
#       --database-version=POSTGRES_16 --region="$REGION" \
#       --tier=db-f1-micro --storage-size=10
#   gcloud sql databases create "$DB_NAME" --instance="$SQL_INSTANCE_NAME"
#   gcloud sql users create "$DB_USER" --instance="$SQL_INSTANCE_NAME" \
#       --password="$DB_PASSWORD"
#   # Mint and upload secrets (one-off):
#   ./scripts/generate-secrets.sh > /tmp/nowgo.env
#   while IFS='=' read -r k v; do
#     [ -z "$k" ] || [[ "$k" == \#* ]] && continue
#     echo -n "$v" | gcloud secrets create "$k" --data-file=- 2>/dev/null \
#       || echo -n "$v" | gcloud secrets versions add "$k" --data-file=-
#   done < /tmp/nowgo.env
#   shred -u /tmp/nowgo.env
#
# Required env vars for this script:
#   GCP_PROJECT          GCP project id
#   REGION               default: southamerica-east1
#   AR_REPO              default: nowgo-saude
#   SERVICE              default: nowgo-saude-backend
#   SQL_INSTANCE         PROJECT:REGION:INSTANCE  (the connection name)
set -euo pipefail

: "${GCP_PROJECT:?set GCP_PROJECT}"
: "${SQL_INSTANCE:?set SQL_INSTANCE (format PROJECT:REGION:INSTANCE)}"
REGION="${REGION:-southamerica-east1}"
AR_REPO="${AR_REPO:-nowgo-saude}"
SERVICE="${SERVICE:-nowgo-saude-backend}"

IMAGE="${REGION}-docker.pkg.dev/${GCP_PROJECT}/${AR_REPO}/backend:$(git rev-parse --short HEAD)"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

echo "==> building ${IMAGE}"
gcloud builds submit "${ROOT}" --tag "${IMAGE}" --region "${REGION}" --project "${GCP_PROJECT}"

echo "==> deploying migration job"
gcloud run jobs deploy "${SERVICE}-migrate" \
  --image="${IMAGE}" \
  --region="${REGION}" \
  --project="${GCP_PROJECT}" \
  --command=alembic --args=upgrade,head \
  --set-cloudsql-instances="${SQL_INSTANCE}" \
  --set-secrets=NOWGO_DATABASE_URL=NOWGO_DATABASE_URL:latest,NOWGO_PII_TOKEN_SECRET=NOWGO_PII_TOKEN_SECRET:latest,NOWGO_PII_VAULT_KEY=NOWGO_PII_VAULT_KEY:latest \
  --max-retries=1 --quiet

echo "==> running migrations"
gcloud run jobs execute "${SERVICE}-migrate" \
  --region="${REGION}" --project="${GCP_PROJECT}" --wait --quiet

echo "==> deploying service ${SERVICE}"
gcloud run deploy "${SERVICE}" \
  --image="${IMAGE}" \
  --region="${REGION}" \
  --project="${GCP_PROJECT}" \
  --platform=managed \
  --port=8000 \
  --allow-unauthenticated \
  --add-cloudsql-instances="${SQL_INSTANCE}" \
  --set-env-vars=NOWGO_ENVIRONMENT=production \
  --set-secrets=NOWGO_DATABASE_URL=NOWGO_DATABASE_URL:latest,NOWGO_ADMIN_TOKEN=NOWGO_ADMIN_TOKEN:latest,NOWGO_LGPD_OFFICER_TOKEN=NOWGO_LGPD_OFFICER_TOKEN:latest,NOWGO_PII_TOKEN_SECRET=NOWGO_PII_TOKEN_SECRET:latest,NOWGO_PII_VAULT_KEY=NOWGO_PII_VAULT_KEY:latest,NOWGO_PII_VAULT_KEY_VERSION=NOWGO_PII_VAULT_KEY_VERSION:latest \
  --min-instances=0 --max-instances=4 \
  --memory=512Mi --cpu=1 --timeout=60 \
  --quiet

URL="$(gcloud run services describe "${SERVICE}" --region="${REGION}" \
  --project="${GCP_PROJECT}" --format='value(status.url)')"

echo
echo "==> service deployed: ${URL}"
echo "==> smoke test:"
echo "    curl ${URL}/health"
