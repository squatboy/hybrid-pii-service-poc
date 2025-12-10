import logging
from fastapi import FastAPI
from app.core.config import settings
from app.routers import health


# 로그 필터링
class HealthCheckFilter(logging.Filter):
    """GET /health 요청이 200 OK로 응답하면 로그를 기록하지 않음"""

    def filter(self, record: logging.LogRecord) -> bool:
        try:
            msg = record.getMessage()
            # /health 경로 요청이 200 OK인 경우 필터링
            if "/health" in msg and "200 OK" in msg:
                return False
            if "/health" in msg and "200" in msg:
                return False
        except Exception:
            pass
        return True


# 모든 uvicorn 로거에 필터 적용
for logger_name in ["uvicorn.access", "uvicorn"]:
    logger = logging.getLogger(logger_name)
    logger.addFilter(HealthCheckFilter())

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
        return {
            "error": "Access Denied: PII operations are not allowed in Cloud environment."
        }


if __name__ == "__main__":
    import uvicorn

    print(f"Starting server on port {settings.PORT}...")
    uvicorn.run(app, host="0.0.0.0", port=settings.PORT)
