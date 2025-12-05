from fastapi import FastAPI
from app.core.config import settings
from app.routers import health

app = FastAPI(title=settings.PROJECT_NAME)

# 1. 공통 라우터 (Health Check) - 어디서든 동작
app.include_router(health.router)

# 2. 환경별 라우터 분기 (핵심 로직)
if settings.IS_ONPREM:
    print(f"🚀 [Startup] ON-PREMISE Mode Detected. Enabling PII Routers...")
    from app.routers import pii
    app.include_router(pii.router)
else:
    print(f"☁️ [Startup] CLOUD Mode Detected. PII Routers are DISABLED.")
    
    # 클라우드용 더미 라우터 (보안 강화: PII 경로 요청 시 명확한 거절 메시지)
    @app.api_route("/pii/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
    def block_pii_requests(path: str):
        return {"error": "Access Denied: PII operations are not allowed in Cloud environment."}

if __name__ == "__main__":
    import uvicorn
    print(f"Starting server on port {settings.PORT}...")
    uvicorn.run(app, host="0.0.0.0", port=settings.PORT)
