import threading
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import OperationalError
from app.core.security import get_db_credentials
from app.core.config import settings

# 전역 변수
_engine = None
_SessionLocal = None
_pool_lock = threading.Lock()  # 스레드 경합 방지용 락


def _init_db_pool():
    """
    Vault에서 Credential을 조회하고 Connection Pool 생성.
    기존 Pool이 있으면 정리 후 새로 생성 (비밀번호 Rotation 대응).
    """
    global _engine, _SessionLocal

    # 락을 걸어 중복 갱신 방지
    with _pool_lock:
        # 기존 엔진이 있다면 연결 종료 (리소스 정리)
        if _engine is not None:
            print("🔄 [Database] Disposing old connection pool...")
            _engine.dispose()

        try:
            # Vault에서 비밀번호 가져옴
            creds = get_db_credentials()

            # Connection String 생성
            DATABASE_URL = f"mysql+pymysql://{creds['user']}:{creds['password']}@{creds['host']}:{creds['port']}/{creds['db']}"

            # Connection Pool이 포함된 엔진 생성
            _engine = create_engine(
                DATABASE_URL,
                pool_size=5,  # 기본 연결 수
                max_overflow=10,  # 추가 허용 연결 수
                pool_timeout=30,  # 연결 대기 타임아웃 (초)
                pool_recycle=1800,  # 연결 재활용 주기 (30분, MySQL wait_timeout 대응)
                pool_pre_ping=True,  # 연결 전 Ping 테스트 (Stale Connection 방지)
            )
            _SessionLocal = sessionmaker(
                autocommit=False, autoflush=False, bind=_engine
            )
            print("✅ [Database] Connection Pool initialized successfully.")

        except Exception as e:
            print(f"❌ [Database] Failed to initialize pool: {str(e)}")
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
            print(
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
