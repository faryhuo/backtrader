from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from src.routes.common.auth_dependencies import get_optional_user_id
from src.service.ai_service import call_ai

router = APIRouter()


@router.post("/ai_analyze")
async def analyze_chart(
    message: str = Form(...),
    model: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    user_id: str = Depends(get_optional_user_id),
):
    try:
        image_bytes = await file.read() if file is not None else None
        return await call_ai(
            message,
            user_id=user_id,
            model=model,
            image_bytes=image_bytes,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
