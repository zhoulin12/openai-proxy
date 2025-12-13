# api/proxy.py 内容
from http.client import HTTPException
import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import httpx

app = FastAPI()

# 允许跨域请求（方便本地调试）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 从 Vercel 环境变量读取 OpenAI Key（最安全的方式）
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
OPENAI_BASE_URL = "https://api.openai.com/v1"

@app.post("/v1/chat/completions")
async def proxy_to_openai(request: dict):
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            # 关键：将请求转发给真正的 OpenAI API
            response = await client.post(
                f"{OPENAI_BASE_URL}/chat/completions",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {OPENAI_API_KEY}"
                },
                json=request
            )
            return response.json()
        except httpx.TimeoutException:
            raise HTTPException(status_code=504, detail="请求超时")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"代理服务错误: {str(e)}")

@app.get("/")
async def root():
    return {"message": "OpenAI 反向代理服务运行正常"}