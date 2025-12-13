import boto3
import json
import logging

logger = logging.getLogger("uvicorn")


def get_secret(secret_arn: str, region_name: str = "ap-northeast-2") -> dict:
    """
    AWS Secrets Manager에서 Secret Value(JSON)를 가져옵니다.
    """
    session = boto3.session.Session()
    client = session.client(service_name="secretsmanager", region_name=region_name)

    try:
        logger.info(f"🔐 [AWS Secrets] Fetching secret from: {secret_arn}")
        get_secret_value_response = client.get_secret_value(SecretId=secret_arn)
    except Exception as e:
        logger.error(f"❌ [AWS Secrets Error] Failed to fetch secret: {str(e)}")
        raise e

    if "SecretString" in get_secret_value_response:
        secret = get_secret_value_response["SecretString"]
        return json.loads(secret)
    else:
        # Binary secret인 경우 (거의 안 씀)
        raise Exception("Binary secret not supported")
