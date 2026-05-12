"""PII triage over telemetry_events.text_anonymized in production.

Reads NOWGO_DATABASE_URL from Secret Manager, rewrites the host to the
local Cloud SQL Auth Proxy (127.0.0.1:5544), and runs read-only checks.
Does not print credentials. Reports counts + sanitized samples.

Usage:
  /tmp/cloud-sql-proxy --gcloud-auth --port 5544 \
      nowgo-saude-prod:southamerica-east1:nowgo-saude-pg &
  python -m scripts.pii_triage
"""
from __future__ import annotations

import re
import subprocess
import sys
from urllib.parse import urlparse, urlunparse

import psycopg


def secret(name: str) -> str:
    out = subprocess.run(
        ["gcloud", "secrets", "versions", "access", "latest",
         f"--secret={name}", "--project=nowgo-saude-prod"],
        check=True, capture_output=True, text=True,
    )
    return out.stdout.strip()


def rewrite_for_proxy(url: str, host: str = "127.0.0.1", port: int = 5544) -> str:
    p = urlparse(url)
    userinfo = ""
    if p.username:
        userinfo = p.username
        if p.password:
            userinfo += f":{p.password}"
        userinfo += "@"
    return urlunparse(("postgresql", f"{userinfo}{host}:{port}", p.path, "", "", ""))


PII_PATTERNS = {
    "cpf_11d":     r"[0-9]{3}\.?[0-9]{3}\.?[0-9]{3}-?[0-9]{2}",
    "phone_br":    r"\(?[0-9]{2}\)?[ ]?9?[0-9]{4}-?[0-9]{4}",
    "email":       r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
    "cep":         r"[0-9]{5}-?[0-9]{3}",
    "rg_like":     r"[0-9]{1,2}\.[0-9]{3}\.[0-9]{3}-?[0-9xX]",
    "long_digits": r"[0-9]{8,}",
}


def main() -> int:
    raw_url = secret("NOWGO_DATABASE_URL")
    proxy_url = rewrite_for_proxy(raw_url)

    with psycopg.connect(proxy_url, connect_timeout=10) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT count(*), min(received_at), max(received_at) FROM telemetry_events")
            total, t_min, t_max = cur.fetchone()
            print(f"telemetry_events total={total} range=[{t_min} .. {t_max}]")

            cur.execute(
                "SELECT status, count(*) FROM telemetry_events GROUP BY status ORDER BY 2 DESC"
            )
            print("by status:", cur.fetchall())

            cur.execute(
                "SELECT count(*) FROM telemetry_events "
                "WHERE text_anonymized IS NOT NULL AND length(text_anonymized) > 0"
            )
            (n_anon,) = cur.fetchone()
            print(f"with text_anonymized: {n_anon}")

            print("\n--- PII pattern sweep (anonymized column, whole table) ---")
            for label, pat in PII_PATTERNS.items():
                cur.execute(
                    "SELECT count(*) FROM telemetry_events WHERE text_anonymized ~ %s",
                    (pat,),
                )
                (hits,) = cur.fetchone()
                marker = "FAIL" if hits > 0 else "ok"
                print(f"  [{marker}] {label:<14} hits={hits}")

            print("\n--- pii_tokens column inspection ---")
            # Constitutional: text_anonymized stores ONLY redacted text;
            # pii_tokens stores the tokens that replaced detected PII.
            # If any row has anonymizer markers inside text_anonymized
            # ([CPF], [PHONE], [NAME], [EMAIL]) but pii_tokens is empty,
            # that's a write-side bug.
            cur.execute(
                "SELECT count(*) FROM telemetry_events "
                "WHERE pii_tokens IS NULL OR jsonb_typeof(pii_tokens::jsonb) <> 'array'"
            )
            (bad_tokens,) = cur.fetchone()
            print(f"  rows with malformed pii_tokens: {bad_tokens}")

            cur.execute(
                "SELECT count(*) FROM telemetry_events "
                "WHERE jsonb_array_length(pii_tokens::jsonb) > 0"
            )
            (with_tokens,) = cur.fetchone()
            print(f"  rows with non-empty pii_tokens: {with_tokens}")

            cur.execute(
                "SELECT count(*) FROM telemetry_events "
                "WHERE text_anonymized ~ '\\[(CPF|PHONE|NAME|EMAIL|CEP|RG)\\]'"
            )
            (marker_rows,) = cur.fetchone()
            print(f"  rows with [TOKEN] markers in text: {marker_rows}")

            print("\n--- 15 most recent anonymized samples (visual triage) ---")
            cur.execute(
                "SELECT received_at, topic, status, "
                "       substring(text_anonymized for 200) "
                "FROM telemetry_events "
                "WHERE text_anonymized IS NOT NULL AND length(text_anonymized) > 0 "
                "ORDER BY received_at DESC LIMIT 15"
            )
            for ts, topic, status, txt in cur.fetchall():
                print(f"  [{ts}] topic={topic} status={status}")
                print(f"    {txt!r}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
