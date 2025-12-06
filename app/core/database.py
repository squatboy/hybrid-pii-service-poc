from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.security import get_db_credentials
from app.core.config import settings

# 전역 변수: Connection Pool (앱 시작 시 1회 초기화)
_engine = None
_SessionLocal = None


def _init_db_pool():
    """
    앱 시작 시 Vault에서 Credential을 1회 조회하고 Connection Pool 생성.
    이후 요청들은 Pool에서 연결을 재사용함 (성능 최적화).
    """
    global _engine, _SessionLocal
    
    if _engine is not None:
        return  # 이미 초기화됨
    
    # 1. Vault에서 비밀번호 가져오기 (1회만)
    creds = get_db_credentials()
    
    # 2. Connection String 생성
    DATABASE_URL = f"mysql+pymysql://{creds['user']}:{creds['password']}@{creds['host']}:{creds['port']}/{creds['db']}"
    
    # 3. Connection Pool이 포함된 엔진 생성
    _engine = create_engine(
        DATABASE_URL,
        pool_size=5,           # 기본 연결 수
        max_overflow=10,       # 추가 허용 연결 수
        pool_timeout=30,       # 연결 대기 타임아웃 (초)
        pool_recycle=1800,     # 연결 재활용 주기 (30분)
        pool_pre_ping=True     # 연결 유효성 검사
    )
    _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)
    
    print("✅ [Database] Connection Pool initialized successfully.")


def get_db_session():
    """
    Connection Pool에서 세션을 가져와 반환.
    요청 완료 후 세션을 Pool에 반환 (연결 유지).
    """
    # Pool이 없으면 초기화 (Lazy Initialization)
    if _engine is None:
        _init_db_pool()
    
    db = _SessionLocal()
    try:
        yield db
    finally:
        db.close()  # Pool에 연결 반환 (연결 끊지 않음)
