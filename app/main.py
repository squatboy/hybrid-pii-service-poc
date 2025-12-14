import logging
from fastapi import FastAPI
from app.core.config import settings
from app.core.database import Base, engine
from app.routers import health

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

# 1. 공통 라우터 (Health Check) - 어디서든 동작
app.include_router(health.router)

# 2. 환경별 라우터 분기 (조건부 import로 모델 로딩 제어)
if settings.IS_ONPREM:
    logger.info("🏢 [Startup] ON-PREMISE Mode Detected.")
    from app.routers import pii as pii_router
    from app.models import pii as pii_models
    app.include_router(pii_router.router)
else:
    logger.info("☁️ [Startup] CLOUD Mode Detected.")
    from app.routers import bookings as bookings_router
    from app.models import booking as booking_models
    app.include_router(bookings_router.router)

# 데이터베이스 테이블 자동 생성 (환경별 모델 로드 후 실행)
Base.metadata.create_all(bind=engine)


if __name__ == "__main__":
    import uvicorn

    print(f"Starting server on port {settings.PORT}...")
    uvicorn.run(app, host="0.0.0.0", port=settings.PORT)
