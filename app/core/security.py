import logging
import hvac
from app.core.config import settings

logger = logging.getLogger("uvicorn")


def get_db_credentials():
    """
    Vault에 AppRole로 로그인하여 DB 접속 정보를 가져옴.
    이 함수는 온프레미스 환경에서만 호출되어야 함.
    """
    # Cloud 모드이거나 ID가 없으면 에러
    if not settings.IS_ONPREM:
        raise RuntimeError("Vault access is NOT allowed in Cloud mode.")

    if not settings.VAULT_ROLE_ID or not settings.VAULT_SECRET_ID:
        raise ValueError("Vault Credentials (RoleID/SecretID) are missing!")

    client = hvac.Client(url=settings.VAULT_ADDR)

    try:
        # 1. AppRole 로그인
        logger.info(f"🔐 [Vault] Connecting to {settings.VAULT_ADDR}...")
        client.auth.approle.login(
            role_id=settings.VAULT_ROLE_ID, secret_id=settings.VAULT_SECRET_ID
        )

        # 2. Secret 조회 (KV Engine v2 기준)
        # mount_point='secret', path='pii-db'
        read_response = client.secrets.kv.v2.read_secret_version(path="pii-db")

        # 3. 데이터 추출 (kv v2는 data['data']['data'] 구조일 수 있음, hvac 버전에 따라 data['data']일수도 있음)
        # 보통 hvac read_secret_version 응답의 'data' 키 안에 실제 secret data가 'data' 키로 들어있음
        secret_payload = read_response["data"]["data"]

        logger.info("✅ [Vault] DB Credentials retrieved successfully.")

        return {
            "user": secret_payload["username"],
            "password": secret_payload["password"],
            "host": secret_payload.get("host", "10.10.10.10"),
            "port": int(secret_payload.get("port", 3306)),
            "db": "pii_db",
        }

    except Exception as e:
        logger.error(f"❌ [Vault Error] Failed to get secrets: {str(e)}")
        raise e
