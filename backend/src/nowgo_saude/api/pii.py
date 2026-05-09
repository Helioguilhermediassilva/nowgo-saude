"""PII re-identification endpoint (LGPD-restricted)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..schemas import PiiReidentifyRequest, PiiReidentifyResponse
from ..services.pii_vault import VaultError, reidentify
from .deps import db_session, require_lgpd_officer

router = APIRouter(prefix="/api/v1/pii", tags=["pii"])


@router.post("/{token}", response_model=PiiReidentifyResponse)
def reidentify_token(
    token: str,
    payload: PiiReidentifyRequest,
    session: Session = Depends(db_session),
    actor: str = Depends(require_lgpd_officer),
) -> PiiReidentifyResponse:
    """Decrypt the original PII for ``token`` and audit the access.

    Restricted to the LGPD officer role; every successful call appends an
    immutable ``pii.reidentify`` row to ``audit_entries``.
    """
    try:
        result = reidentify(
            session,
            token,
            actor_id=actor,
            actor_role="lgpd_officer",
            reason=payload.reason,
        )
    except VaultError as exc:
        session.rollback()
        msg = str(exc)
        if msg.startswith("unknown vault token"):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "token_not_found", "message": msg},
            ) from exc
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "vault_error", "message": msg},
        ) from exc
    session.commit()
    return PiiReidentifyResponse(
        token=result.token,
        category=result.category,  # type: ignore[arg-type]
        value=result.value,
        key_version=result.key_version,
        first_seen_at=result.first_seen_at,
        last_seen_at=result.last_seen_at,
        usage_count=result.usage_count,
    )
