import logging
from fastapi import FastAPI
from app.core.config import settings
from app.routers import health, pii, bookings
from app.core.database import Base, engine

# 환경에 따라 필요한 모델만 로드
if settings.IS_ONPREM:
    from app.models import pii as pii_models
else:
    from app.models import booking as booking_models

logger = logging.getLogger("uvicorn")


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

# 데이터베이스 테이블 자동 생성 (앱 시작 시)
Base.metadata.create_all(bind=engine)

# 1. 공통 라우터 (Health Check) - 어디서든 동작
app.include_router(health.router)

# 2. 환경별 라우터 분기 (핵심 로직)
if settings.IS_ONPREM:
    logger.info("🏢 [Startup] ON-PREMISE Mode: PII Router Activated.")
    app.include_router(pii.router)
else:
    logger.info("☁️ [Startup] CLOUD Mode: Booking Router Activated.")
    app.include_router(bookings.router)


if __name__ == "__main__":
    import uvicorn

    print(f"Starting server on port {settings.PORT}...")
    uvicorn.run(app, host="0.0.0.0", port=settings.PORT)
