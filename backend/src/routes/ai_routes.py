import base64
from typing import Optional

import httpx
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from openai import AsyncOpenAI

from src.config.config_manager import ConfigManager
from src.routes.common.auth_dependencies import get_optional_user_id

router = APIRouter()

def encode_image(image_file):
    return base64.b64encode(image_file).decode("utf-8")


@router.post("/ai_analyze")
async def analyze_chart(
    message: str = Form(...),
    model: str = Form("gpt-4o"),
    file: Optional[UploadFile] = File(None),
    user_id: str = Depends(get_optional_user_id),
):
    try:
        # Get user-specific configuration with database fallback
        
        config_manager = ConfigManager(user_id=user_id)

        # Get OpenAI and proxy configuration
        openai_config = config_manager.get_openai_config()
        proxy_config = config_manager.get_proxy_config()

        api_key = openai_config.get("api_key")
        base_url = openai_config.get("base_url")

        if not api_key or not base_url:
            raise HTTPException(
                status_code=500,
                detail="OpenAI API credentials not configured. Please configure them in Settings or set OPENAI_API_KEY/OPENAI_BASE_URL in .env"
            )

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

        proxy = proxy_config.get("https_proxy") or proxy_config.get("http_proxy")
        # Build OpenAI client; wrap in httpx client when a proxy is configured.
        if proxy:
            async with httpx.AsyncClient(proxy=proxy, timeout=900) as http_client:
                client = AsyncOpenAI(
                    api_key=api_key,
                    base_url=base_url,
                    http_client=http_client,
                )
                response = await client.chat.completions.create(
                    model=model,
                    messages=messages,
                )
        else:
            client = AsyncOpenAI(api_key=api_key, base_url=base_url)

            response = await client.chat.completions.create(
                model=model,
                messages=messages,
            )

        analysis = response.choices[0].message.content
        return {"analysis": analysis}

    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
