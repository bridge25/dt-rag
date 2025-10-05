from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends, status, Request
from fastapi.responses import JSONResponse
from typing import Optional, List
import logging
import uuid

from apps.ingestion.contracts.signals import (
    DocumentUploadCommandV1,
    DocumentFormatV1,
    JobStatusQueryV1,
    JobStatusResponseV1,
    ProcessingStatusV1,
)
from apps.ingestion.batch import JobOrchestrator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ingestion", tags=["Ingestion"])

_job_orchestrator: Optional[JobOrchestrator] = None


async def get_job_orchestrator() -> JobOrchestrator:
    global _job_orchestrator
    if _job_orchestrator is None:
        _job_orchestrator = JobOrchestrator(max_workers=100)
        await _job_orchestrator.start()
    return _job_orchestrator


@router.post(
    "/upload",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Upload document for processing",
)
async def upload_document(
    file: UploadFile = File(...),
    taxonomy_path: str = Form(...),
    source_url: Optional[str] = Form(None),
    author: Optional[str] = Form(None),
    language: str = Form("ko"),
    priority: int = Form(5),
    orchestrator: JobOrchestrator = Depends(get_job_orchestrator),
    http_request: Request = None,
):
    try:
        correlation_id = http_request.headers.get("X-Correlation-ID") if http_request else str(uuid.uuid4())
        if not correlation_id:
            correlation_id = str(uuid.uuid4())

        file_extension = file.filename.split(".")[-1].lower()

        try:
            file_format = DocumentFormatV1(file_extension)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file format: {file_extension}. Supported formats: pdf, docx, csv, html, txt",
            )

        file_content = await file.read()

        if len(file_content) > 50 * 1024 * 1024:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File size exceeds 50MB limit",
            )

        taxonomy_path_list = [p.strip() for p in taxonomy_path.split(",")]

        if not taxonomy_path_list or len(taxonomy_path_list) > 10:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Taxonomy path must have 1-10 elements",
            )

        command = DocumentUploadCommandV1(
            correlationId=correlation_id,
            file_name=file.filename,
            file_content=file_content,
            file_format=file_format,
            taxonomy_path=taxonomy_path_list,
            source_url=source_url,
            author=author,
            language=language,
            priority=priority,
        )

        job_id = await orchestrator.submit_job(command)

        estimated_completion_minutes = max(1, len(file_content) // (1024 * 1024))

        return JSONResponse(
            status_code=status.HTTP_202_ACCEPTED,
            content={
                "job_id": job_id,
                "correlation_id": correlation_id,
                "status": "pending",
                "estimated_completion_minutes": estimated_completion_minutes,
                "message": "Document accepted for processing",
            },
            headers={
                "X-Job-ID": job_id,
                "X-Correlation-ID": correlation_id
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to upload document: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process upload",
        )


@router.get(
    "/status/{job_id}",
    response_model=JobStatusResponseV1,
    summary="Get ingestion job status",
)
async def get_job_status(
    job_id: str,
    orchestrator: JobOrchestrator = Depends(get_job_orchestrator),
):
    try:
        status_data = await orchestrator.get_job_status(job_id)

        if not status_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found",
            )

        response = JobStatusResponseV1(**status_data)

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get job status for {job_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve job status",
        )


@router.on_event("shutdown")
async def shutdown_event():
    global _job_orchestrator
    if _job_orchestrator is not None:
        await _job_orchestrator.stop()
        _job_orchestrator = None
        logger.info("Job Orchestrator shutdown complete")
