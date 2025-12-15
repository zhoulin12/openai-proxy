from http.client import HTTPException
import os
from fastapi import FastAPI, HTTPException, Request  # 导入 Request 用于获取请求头
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

# 从 Vercel 环境变量读取密钥
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
# 🔐 新增：从环境变量读取你自己的访问密钥
YOUR_SECRET_TOKEN = os.environ.get("YOUR_SECRET_TOKEN")
OPENAI_BASE_URL = "https://api.openai.com/v1"

@app.post("/v1/chat/completions")
async def proxy_to_openai(request: Request):  # 修改参数为 Request 对象
    # 🔐 新增：第一步，验证客户端密钥
    client_token = request.headers.get("X-API-Key")
    if not YOUR_SECRET_TOKEN:
        # 如果服务器未设置密钥，拒绝所有请求（安全兜底）
        raise HTTPException(status_code=500, detail="Server configuration error")
    if client_token != YOUR_SECRET_TOKEN:
        # 密钥不匹配，返回 403 禁止访问
        raise HTTPException(status_code=403, detail="Forbidden: Invalid or missing API Key")
    
    # 🔐 验证通过，继续处理
    try:
        # 获取客户端发送的 JSON 请求体
        request_body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            # 转发给 OpenAI
            response = await client.post(
                f"{OPENAI_BASE_URL}/chat/completions",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {OPENAI_API_KEY}"
                },
                json=request_body  # 使用解析后的请求体
            )
            return response.json()
        except httpx.TimeoutException:
            raise HTTPException(status_code=504, detail="请求超时")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"代理服务错误: {str(e)}")

@app.get("/")
async def root():
    return {"message": "OpenAI 反向代理服务运行正常"}