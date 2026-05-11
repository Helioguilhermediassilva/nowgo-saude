#!/usr/bin/env bash
# One-shot helper that runs scripts/seed_demo.py against the production
# Cloud SQL instance via a transient Cloud Run Job.
#
# Reuses the same image already pushed by deploy-cloud-run.sh, so call this
# AFTER a successful service deploy. The job is idempotent (events are tagged
# with attributes.seed_tag = 'demo-v1' and skipped on re-run) and is left in
# place between executions so re-seeding is just `gcloud run jobs execute`.
#
# Required env vars:
#   GCP_PROJECT          GCP project id
#   SQL_INSTANCE         PROJECT:REGION:INSTANCE  (the connection name)
# Optional:
#   REGION               default: southamerica-east1
#   SERVICE              default: nowgo-saude-backend
#   IMAGE                default: latest image tagged in Artifact Registry
#   SEED_EVENTS          default: 6000
#   SEED_HOURS_BACK      default: 336  (14 days)
#   SEED_VALUE           default: 20260509
set -euo pipefail

: "${GCP_PROJECT:?set GCP_PROJECT}"
: "${SQL_INSTANCE:?set SQL_INSTANCE (format PROJECT:REGION:INSTANCE)}"
REGION="${REGION:-southamerica-east1}"
AR_REPO="${AR_REPO:-nowgo-saude}"
SERVICE="${SERVICE:-nowgo-saude-backend}"
JOB="${SERVICE}-seed-demo"
SEED_EVENTS="${SEED_EVENTS:-6000}"
SEED_HOURS_BACK="${SEED_HOURS_BACK:-336}"
SEED_VALUE="${SEED_VALUE:-20260509}"
SEED_REFRESH="${SEED_REFRESH:-0}"

ARGS="scripts/seed_demo.py,--events,${SEED_EVENTS},--hours-back,${SEED_HOURS_BACK},--seed,${SEED_VALUE}"
if [[ "${SEED_REFRESH}" == "1" ]]; then
  ARGS="${ARGS},--refresh"
fi

if [[ -z "${IMAGE:-}" ]]; then
  # Resolve the image currently serving the Cloud Run service so the seed
  # always runs the same code that exposes the dashboard endpoints.
  IMAGE="$(gcloud run services describe "${SERVICE}" \
    --region="${REGION}" --project="${GCP_PROJECT}" \
    --format='value(spec.template.spec.containers[0].image)')"
fi

echo "==> deploying seed job ${JOB}"
echo "    image:  ${IMAGE}"
echo "    events: ${SEED_EVENTS}  hours_back: ${SEED_HOURS_BACK}  seed: ${SEED_VALUE}"
gcloud run jobs deploy "${JOB}" \
  --image="${IMAGE}" \
  --region="${REGION}" \
  --project="${GCP_PROJECT}" \
  --command=python \
  --args="${ARGS}" \
  --set-cloudsql-instances="${SQL_INSTANCE}" \
  --set-secrets=NOWGO_DATABASE_URL=NOWGO_DATABASE_URL:latest,NOWGO_PII_TOKEN_SECRET=NOWGO_PII_TOKEN_SECRET:latest,NOWGO_PII_VAULT_KEY=NOWGO_PII_VAULT_KEY:latest,NOWGO_PII_VAULT_KEY_VERSION=NOWGO_PII_VAULT_KEY_VERSION:latest \
  --max-retries=1 --task-timeout=600 --quiet

echo "==> running seed job"
gcloud run jobs execute "${JOB}" \
  --region="${REGION}" --project="${GCP_PROJECT}" --wait --quiet

echo
echo "==> done. To re-seed (idempotent) without redeploying:"
echo "    gcloud run jobs execute ${JOB} --region=${REGION} --project=${GCP_PROJECT} --wait"
