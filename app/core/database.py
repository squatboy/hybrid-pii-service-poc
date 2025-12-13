import logging
import threading
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.exc import OperationalError
from app.core.security import get_db_credentials
from app.core.config import settings

logger = logging.getLogger("uvicorn")

# SQLAlchemy ORM 기본 클래스
Base = declarative_base()

# 전역 변수
_engine = None
_SessionLocal = None
_pool_lock = threading.Lock()  # 스레드 경합 방지용 락


def _init_db_pool():
    """
    DB 접속 정보를 가져오고 Connection Pool 생성.
    - Cloud 환경: settings.DATABASE_URL이 이미 설정됨 (config.py에서 AWS Secrets Manager에서 로드)
    - On-Prem 환경: Vault에서 Credential을 조회하여 CONNECTION_STRING 생성
    기존 Pool이 있으면 정리 후 새로 생성 (비밀번호 Rotation 대응).
    """
    global _engine, _SessionLocal

    # 락을 걸어 중복 갱신 방지
    with _pool_lock:
        # 기존 엔진이 있다면 연결 종료 (리소스 정리)
        if _engine is not None:
            logger.info("🔄 [Database] Disposing old connection pool...")
            _engine.dispose()

        try:
            # DATABASE_URL 결정
            if settings.DATABASE_URL:
                # Cloud 모드: 이미 config.py에서 로드됨
                DATABASE_URL = settings.DATABASE_URL
                logger.info("☁️ [Database] Using Cloud Mode (AWS Secrets Manager)")
            else:
                # On-Prem 모드: Vault에서 조회
                creds = get_db_credentials()
                DATABASE_URL = f"mysql+pymysql://{creds['user']}:{creds['password']}@{creds['host']}:{creds['port']}/{creds['db']}"
                logger.info("🏢 [Database] Using On-Premise Mode (Vault)")

            # Connection Pool이 포함된 엔진 생성
            _engine = create_engine(
                DATABASE_URL,
                pool_size=settings.DB_POOL_SIZE,
                max_overflow=settings.DB_MAX_OVERFLOW,
                pool_timeout=30,  # 연결 대기 타임아웃 (초)
                pool_recycle=1800,  # 연결 재활용 주기 (30분, MySQL wait_timeout 대응)
                pool_pre_ping=True,  # 연결 전 Ping 테스트 (Stale Connection 방지)
            )
            _SessionLocal = sessionmaker(
                autocommit=False, autoflush=False, bind=_engine
            )
            logger.info("✅ [Database] Connection Pool initialized successfully.")

        except Exception as e:
            logger.error(f"❌ [Database] Failed to initialize pool: {str(e)}")
            raise e


def get_db_session():
    """
    Connection Pool에서 세션을 가져와 반환.
    인증 실패 시 Vault에서 새 Credential을 받아 Pool 재생성 (자동 복구).
    """
    global _SessionLocal

    # Pool이 없으면 초기화 (Lazy Initialization)
    if _SessionLocal is None:
        _init_db_pool()

    db = None
    try:
        db = _SessionLocal()
        # 연결 테스트 (SQLAlchemy 2.0 문법: text() 필수)
        db.execute(text("SELECT 1"))
        yield db
    except OperationalError as e:
        # MySQL 인증 에러 코드: 1045 (Access Denied), 1044 (DB Access Denied)
        error_code = e.orig.args[0] if e.orig and e.orig.args else 0

        if error_code in [1045, 1044]:
            logger.warning(
                f"⚠️ [Database] Authentication failed (error: {error_code}). Refreshing credentials..."
            )

            # 기존 세션 정리
            if db is not None:
                db.close()

            # 비밀번호 갱신 (Pool 재생성)
            _init_db_pool()

            # 새 세션으로 재시도
            db = _SessionLocal()
            yield db
        else:
            # 인증 에러가 아니면 그대로 raise
            raise e
    finally:
        if db is not None:
            db.close()  # Pool에 연결 반환


# 호환성: get_db는 get_db_session의 별칭
def get_db():
    """
    get_db_session의 별칭. FastAPI 라우터에서 Depends(get_db) 형태로 사용 가능.
    """
    yield from get_db_session()


# 초기화: engine 전역 변수 설정 (테이블 생성용)
def get_engine():
    """
    현재 엔진을 반환합니다. 없으면 초기화합니다.
    """
    global _engine
    if _engine is None:
        _init_db_pool()
    return _engine


# 모듈 임포트 시 engine 초기화
engine = get_engine()
