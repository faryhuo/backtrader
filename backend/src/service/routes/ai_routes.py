import base64
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from openai import AsyncOpenAI

from src.config.settings import OPENAI_API_KEY, OPENAI_BASE_URL
from src.utils.auth import get_current_user

router = APIRouter()

def encode_image(image_file):
    return base64.b64encode(image_file).decode("utf-8")


@router.post("/ai_analyze")
async def analyze_chart(
    message: str = Form(...),
    model: str = Form("gpt-4o"),
    file: Optional[UploadFile] = File(None),
    user: dict = Depends(get_current_user),
):
    try:
        if not OPENAI_API_KEY or not OPENAI_BASE_URL:
            raise HTTPException(
                status_code=500,
                detail="OPENAI_API_KEY or OPENAI_BASE_URL not found in environment variables"
            )

        client = AsyncOpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)

        # Prepare content based on whether there's an image
        content: list[dict] = [
            {"type": "text", "text": message},
        ]

        if file is not None:
            contents = await file.read()
            base64_image = encode_image(contents)
            content.append(
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{base64_image}",
                    },
                }
            )

        messages = [
            {
                "role": "user",
                "content": content,
            }
        ]

        response = await client.chat.completions.create(
            model=model,
            messages=messages,
        )

        analysis = response.choices[0].message.content
        return {"analysis": analysis}

    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
