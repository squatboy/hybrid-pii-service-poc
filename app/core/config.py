import os
import logging
from pydantic_settings import BaseSettings
from typing import Optional

logger = logging.getLogger("uvicorn")


class Settings(BaseSettings):
    PROJECT_NAME: str = "Hybrid PII Service PoC"
    ENV: str = "prod"

    # 핵심 스위치: 이 값이 True면 온프레미스 모드로 동작 (Vault/DB 연결 시도)
    IS_ONPREM: bool = os.getenv("IS_ONPREM", "false").lower() == "true"

    # 온프레미스 전용 설정 (Vault)
    VAULT_ADDR: str = "http://127.0.0.1:8200"
    VAULT_ROLE_ID: Optional[str] = None
    VAULT_SECRET_ID: Optional[str] = None

    # DB 설정
    DATABASE_URL: Optional[str] = None

    # AWS Secrets Manager ARN (Terraform 주입)
    DB_SECRET_ARN: Optional[str] = os.getenv("DB_SECRET_ARN")
    AWS_REGION: str = os.getenv("AWS_REGION", "ap-northeast-2")

    # DB Connection Pool 설정 (Auto Scaling 대비)
    DB_POOL_SIZE: int = int(os.getenv("DB_POOL_SIZE", "5"))
    DB_MAX_OVERFLOW: int = int(os.getenv("DB_MAX_OVERFLOW", "10"))

    # 웹 서버 설정
    PORT: int = 8000

    # [신규 추가] 온프레미스 서비스 주소 (VPN 내부 IP)
    ONPREM_SERVICE_URL: str = os.getenv("ONPREM_SERVICE_URL", "http://10.10.10.20:8000")

    # [신규 추가] 내부 통신용 보안 토큰
    INTERNAL_API_TOKEN: str = os.getenv("INTERNAL_API_TOKEN", "my-secret-token")

    def __init__(self, **values):
        super().__init__(**values)
        self._load_db_config()

    def _load_db_config(self):
        """환경에 따라 DB 접속 정보를 동적으로 로드"""
        if not self.IS_ONPREM:
            # [Cloud] AWS Secrets Manager 사용
            if self.DB_SECRET_ARN:
                try:
                    from app.core.aws_secrets import get_secret

                    secrets = get_secret(self.DB_SECRET_ARN, self.AWS_REGION)
                    # Terraform이 저장한 JSON 키: username, password, host, port, dbname
                    user = secrets["username"]
                    password = secrets["password"]
                    host = secrets["host"]
                    port = secrets["port"]
                    dbname = secrets["dbname"]

                    self.DATABASE_URL = (
                        f"mysql+pymysql://{user}:{password}@{host}:{port}/{dbname}"
                    )
                    logger.info(
                        "✅ [Config] Cloud Mode: Loaded DB credentials from AWS Secrets Manager"
                    )
                except Exception as e:
                    logger.error(f"❌ [Config] Failed to load AWS Secret: {e}")
                    raise e
            else:
                logger.warning("⚠️ [Config] DB_SECRET_ARN not found in Cloud Mode.")

        else:
            # [On-Prem] 기존 로직 유지 (Vault 사용)
            logger.info(
                "🏢 [Config] On-Premise Mode: DB credentials will be loaded from Vault at runtime"
            )

    class Config:
        env_file = ".env"
        # 환경변수 대소문자 구분 없음 등 추가 설정 가능


settings = Settings()
