from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.security import get_db_credentials

def get_db_session():
    """
    매 요청마다 Vault에서 Credential을 확인하여 DB 세션을 생성.
    PoC 검증을 위해 매번 연결을 맺고 끊음 (실무에선 Connection Pool 캐싱 고려).
    """
    # 1. Vault에서 비밀번호 가져오기
    creds = get_db_credentials()
    
    # 2. Connection String 생성
    # mysql+pymysql://user:password@host:port/db
    DATABASE_URL = f"mysql+pymysql://{creds['user']}:{creds['password']}@{creds['host']}:{creds['port']}/{creds['db']}"
    
    # 3. 엔진 생성
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        # 엔진도 폐기하여 연결을 완전히 끊음 (PoC용)
        engine.dispose()
