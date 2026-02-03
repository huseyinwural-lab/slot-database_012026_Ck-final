from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Request, UploadFile, File, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.database import get_session
from app.core.errors import AppError
from app.models.game_models import Game
from app.models.game_import_sql import GameImportJob, GameImportItem
from app.services.audit import audit
from app.services.game_import_service import (
    extract_json_bytes,
    normalize_item,
    parse_items,
    store_upload_file_to_tmp,
)
from app.utils.auth import get_current_admin, AdminUser
from app.utils.tenant import get_current_tenant_id


router = APIRouter(prefix="/api/v1/game-import", tags=["game_import"])


def _request_meta(request: Request) -> Dict[str, Optional[str]]:
    return {
        "request_id": getattr(request.state, "request_id", str(uuid.uuid4())),
        "ip_address": getattr(request.state, "ip_address", None),
        "user_agent": getattr(request.state, "user_agent", None),
    }


async def _audit_best_effort(
    *,
    session: AsyncSession,
    request: Request,
    admin: AdminUser,
    tenant_id: str,
    action: str,
    resource_type: str,
    resource_id: Optional[str],
    result: str,
    status: str,
    reason: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    error_code: Optional[str] = None,
    error_message: Optional[str] = None,
) -> None:
    try:
        meta = _request_meta(request)
        await audit.log_event(
            session=session,
            request_id=meta["request_id"],
            actor_user_id=str(admin.id),
            actor_role=getattr(admin, "role", None),
            tenant_id=str(tenant_id),
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            result=result,
            status=status,
            reason=reason,
            ip_address=meta["ip_address"],
            user_agent=meta["user_agent"],
            details=details or {},
            error_code=error_code,
            error_message=error_message,
        )
    except Exception:
        # Never break main flow due to audit.
        try:
            await session.rollback()
        except Exception:
            pass


@router.post("/manual/upload", status_code=201)
async def manual_upload(
    request: Request,
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin),
    file: Optional[UploadFile] = File(None),
    bundle: Optional[UploadFile] = File(None),
    upload: Optional[UploadFile] = File(None),
):
    tenant_id = await get_current_tenant_id(request, current_admin, session=session)

    up = file or bundle or upload
    if not up:
        raise AppError(error_code="MISSING_FILE", message="Missing upload file", status_code=400)

    job = GameImportJob(
        tenant_id=tenant_id,
        created_by_admin_id=str(current_admin.id),
        status="queued",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    session.add(job)
    await session.commit()
    await session.refresh(job)

    await _audit_best_effort(
        session=session,
        request=request,
        admin=current_admin,
        tenant_id=tenant_id,
        action="game_import.upload.attempt",
        resource_type="game_import_job",
        resource_id=job.id,
        result="success",
        status="SUCCESS",
    )

    try:
        stored = await store_upload_file_to_tmp(up, job_id=job.id)
        job.file_name = stored.file_name
        job.file_type = stored.file_type
        job.file_path = stored.path
        job.status = "running"
        job.updated_at = datetime.utcnow()
        session.add(job)
        await session.commit()

        json_bytes = extract_json_bytes(stored)
        raw_items = parse_items(json_bytes)

        items: List[GameImportItem] = []
        errors_preview: List[Dict[str, Any]] = []
        total_errors = 0

        for raw in raw_items:
            external_id, provider_id, name, gtype, rtp, errs = normalize_item(raw)
            status = "valid" if not errs else "invalid"
            if errs:
                total_errors += 1
                if len(errors_preview) < 20:
                    errors_preview.append({"external_id": external_id, "errors": errs})

            items.append(
                GameImportItem(
                    job_id=job.id,
                    tenant_id=tenant_id,
                    provider_id=provider_id,
                    external_id=external_id or "",
                    name=name,
                    type=gtype,
                    rtp=rtp,
                    status=status,
                    errors=errs,
                    payload=raw,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                )
            )

        for it in items:
            session.add(it)

        job.total_items = len(raw_items)
        job.total_errors = total_errors
        job.error_summary = {"preview": errors_preview} if errors_preview else None
        job.status = "ready" if total_errors < len(raw_items) else "failed"
        job.updated_at = datetime.utcnow()
        session.add(job)
        await session.commit()

        await _audit_best_effort(
            session=session,
            request=request,
            admin=current_admin,
            tenant_id=tenant_id,
            action="game_import.uploaded",
            resource_type="game_import_job",
            resource_id=job.id,
            result="success",
            status="SUCCESS",
            details={"total_items": job.total_items, "total_errors": job.total_errors},
        )

        return {"job_id": job.id}

    except ValueError as ve:
        code = str(ve)
        job.status = "failed"
        job.total_items = 0
        job.total_errors = 1
        job.error_summary = {"error": code}
        job.updated_at = datetime.utcnow()
        session.add(job)
        await session.commit()

        await _audit_best_effort(
            session=session,
            request=request,
            admin=current_admin,
            tenant_id=tenant_id,
            action="game_import.upload.failed",
            resource_type="game_import_job",
            resource_id=job.id,
            result="failed",
            status="FAILED",
            error_code=code,
            error_message=code,
        )

        if code == "UPLOAD_TOO_LARGE":
            raise AppError("UPLOAD_TOO_LARGE", "Upload exceeds size limit", 413)
        if code in {"ZIP_NO_JSON", "ZIP_EMPTY", "UNSUPPORTED_FILE"}:
            raise AppError("UNSUPPORTED_FILE", "Unsupported upload format", 400)
        if code in {"JSON_PARSE_ERROR", "JSON_SCHEMA_INVALID"}:
            raise AppError(code, "Invalid JSON bundle", 422)
        if code == "TOO_MANY_ITEMS":
            raise AppError("TOO_MANY_ITEMS", "Too many items in bundle", 413)

        raise AppError("UPLOAD_FAILED", "Upload failed", 500)


@router.get("/jobs/{job_id}")
async def get_job(
    job_id: str,
    request: Request,
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin),
):
    tenant_id = await get_current_tenant_id(request, current_admin, session=session)

    stmt = select(GameImportJob).where(GameImportJob.id == job_id, GameImportJob.tenant_id == tenant_id)
    job = (await session.execute(stmt)).scalars().first()
    if not job:
        raise AppError("NOT_FOUND", "Job not found", 404)

    items_stmt = (
        select(GameImportItem)
        .where(GameImportItem.job_id == job_id, GameImportItem.tenant_id == tenant_id)
        .limit(200)
    )
    items = (await session.execute(items_stmt)).scalars().all()

    await _audit_best_effort(
        session=session,
        request=request,
        admin=current_admin,
        tenant_id=tenant_id,
        action="game_import.job.viewed",
        resource_type="game_import_job",
        resource_id=job.id,
        result="success",
        status="SUCCESS",
    )

    return {
        "job_id": job.id,
        "status": job.status,
        "total_items": job.total_items,
        "total_errors": job.total_errors,
        "error_summary": job.error_summary,
        "items": [
            {
                "id": it.id,
                "external_id": it.external_id,
                "provider_id": it.provider_id,
                "status": it.status,
                "errors": it.errors,
                "name": it.name,
                "type": it.type,
                "rtp": it.rtp,
            }
            for it in items
        ],
    }


@router.post("/jobs/{job_id}/import")
async def import_job(
    job_id: str,
    request: Request,
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin),
):
    tenant_id = await get_current_tenant_id(request, current_admin, session=session)

    stmt = select(GameImportJob).where(GameImportJob.id == job_id, GameImportJob.tenant_id == tenant_id)
    job = (await session.execute(stmt)).scalars().first()
    if not job:
        raise AppError("NOT_FOUND", "Job not found", 404)

    if job.status == "completed":
        return {"status": "completed", "imported_count": job.total_imported}

    if job.status != "ready":
        raise AppError("JOB_NOT_READY", "Job is not ready", 409)

    await _audit_best_effort(
        session=session,
        request=request,
        admin=current_admin,
        tenant_id=tenant_id,
        action="game_import.import.attempt",
        resource_type="game_import_job",
        resource_id=job.id,
        result="success",
        status="SUCCESS",
    )

    items_stmt = select(GameImportItem).where(
        GameImportItem.job_id == job_id,
        GameImportItem.tenant_id == tenant_id,
        GameImportItem.status.in_(["valid", "pending"]),
    )
    items = (await session.execute(items_stmt)).scalars().all()

    imported = 0
    for it in items:
        if it.errors:
            it.status = "skipped"
            it.updated_at = datetime.utcnow()
            session.add(it)
            continue

        provider_id = it.provider_id or (it.payload.get("provider_id") if isinstance(it.payload, dict) else None) or "unknown"
        external_id = it.external_id

        existing_stmt = select(Game).where(
            Game.tenant_id == tenant_id,
            Game.provider_id == provider_id,
            Game.external_id == external_id,
        )
        existing = (await session.execute(existing_stmt)).scalars().first()

        gtype = it.type or "slot"
        rtp = it.rtp if it.rtp is not None else 96.5
        name = it.name or external_id

        if existing:
            existing.name = name
            existing.provider = provider_id
            existing.category = gtype
            existing.type = gtype
            existing.rtp = rtp
            existing.is_active = True
            # Keep configuration; merge payload as snapshot
            try:
                existing.configuration = dict(existing.configuration or {})
                existing.configuration["import_payload"] = it.payload
            except Exception:
                existing.configuration = {"import_payload": it.payload}
            session.add(existing)
        else:
            game = Game(
                tenant_id=tenant_id,
                provider_id=provider_id,
                external_id=external_id,
                type=gtype,
                rtp=rtp,
                is_active=True,
                name=name,
                provider=provider_id,
                category=gtype,
                status="active",
                configuration={"import_payload": it.payload},
            )
            session.add(game)

        it.status = "imported"
        it.updated_at = datetime.utcnow()
        session.add(it)
        imported += 1

    job.total_imported = imported
    job.status = "completed"
    job.updated_at = datetime.utcnow()
    session.add(job)

    await session.commit()

    await _audit_best_effort(
        session=session,
        request=request,
        admin=current_admin,
        tenant_id=tenant_id,
        action="game_import.import.completed",
        resource_type="game_import_job",
        resource_id=job.id,
        result="success",
        status="SUCCESS",
        details={"imported_count": imported},
    )

    return {"status": "completed", "imported_count": imported}


# Legacy route kept for compatibility
@router.post("/import")
async def import_games(
    provider: str = Body(...),
    current_admin: AdminUser = Depends(get_current_admin),
):
    return {"message": f"Import from {provider} queued"}
