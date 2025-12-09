import base64
import os
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from openai import AsyncOpenAI
from dotenv import load_dotenv

router = APIRouter()
load_dotenv()

def encode_image(image_file):
    return base64.b64encode(image_file).decode("utf-8")


@router.post("/ai_analyze")
async def analyze_chart(
    message: str = Form(...),
    model: str = Form("gpt-4o"),
    file: Optional[UploadFile] = File(None),
):
    try:
        # Check if API key is present
        api_key = os.getenv("OPENAI_API_KEY")
        base_url = os.getenv("OPENAI_BASE_URL")
        if not api_key or not base_url:
            raise HTTPException(
                status_code=500,
                detail="OPENAI_API_KEY or OPENAI_BASE_URL not found in environment variables"
            )

        client = AsyncOpenAI(api_key=api_key, base_url=base_url)

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
