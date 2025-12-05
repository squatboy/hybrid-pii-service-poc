from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "Hybrid PII Service PoC"
    ENV: str = "prod"
    
    # 핵심 스위치: 이 값이 True면 온프레미스 모드로 동작 (Vault/DB 연결 시도)
    IS_ONPREM: bool = False
    
    # 온프레미스 전용 설정 (Vault)
    VAULT_ADDR: str = "http://127.0.0.1:8200"
    VAULT_ROLE_ID: Optional[str] = None
    VAULT_SECRET_ID: Optional[str] = None
    
    # 웹 서버 설정
    PORT: int = 8000

    class Config:
        env_file = ".env"
        # 환경변수 대소문자 구분 없음 등 추가 설정 가능

settings = Settings()
