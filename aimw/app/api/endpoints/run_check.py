import os
import tempfile

from app.schemas.response import RunCheckResponse
from app.services.run_check import run_compliance_check
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from loguru import logger

router = APIRouter()


@router.post("/run-check", response_model=RunCheckResponse)
async def run_check(file: UploadFile = File(...), query: str = Form(...)):
    try:
        logger.info(f"Received question: {query}")
        logger.info(f"Received file: {file.filename}")

        suffix = os.path.splitext(file.filename or "")[-1] or ".pdf"

        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name

        logger.info(f"Temp file name: {temp_file_path}")
        logger.info(f"Temp file size: {os.path.getsize(temp_file_path)} bytes")

        answer = run_compliance_check(document_path=temp_file_path, question=query)

        # Ensure answer is a string for Pydantic
        if isinstance(answer, dict) and "answer" in answer:
            answer = str(answer["answer"])

        os.remove(temp_file_path)

        return RunCheckResponse(answer=answer)

    except Exception as e:
        logger.error(f"Error processing request: {e}", exc_info=True)
        if "temp_file_path" in locals() and os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        raise HTTPException(status_code=500, detail=f"Error processing request: {e}")


@router.get("/health")
def health_check():
    return {"status": "OK"}
