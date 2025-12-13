import logging
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models import pii as models
from app.schemas import pii as schemas
from app.core.config import settings

logger = logging.getLogger("uvicorn")

router = APIRouter(prefix="/pii", tags=["PII (On-Premise)"])


# -----------------------------------------------------------------------------
# [Public] PII 생성
# -----------------------------------------------------------------------------
@router.post("/", response_model=schemas.PIIResponse)
def create_pii(pii_in: schemas.PIICreate, db: Session = Depends(get_db)):
    # 암호화 없이 바로 저장
    db_pii = models.UserPII(
        name=pii_in.name,
        email=pii_in.email,
        phone=pii_in.phone,
        passport_no=pii_in.passport_no,
    )
    db.add(db_pii)
    db.commit()
    db.refresh(db_pii)

    return db_pii


# -----------------------------------------------------------------------------
# [Internal] PII 조회
# -----------------------------------------------------------------------------
@router.get("/internal/{user_id}", response_model=schemas.PIIResponse)
def get_internal_pii(
    user_id: str, db: Session = Depends(get_db), x_internal_token: str = Header(None)
):
    """
    [Internal Only] VPN을 통해 접근하는 퍼블릭 클라우드 서비스에 PII 제공
    """
    # 1. 보안 헤더 체크
    expected_token = getattr(settings, "INTERNAL_API_TOKEN", "my-secret-token")

    if x_internal_token != expected_token:
        logger.warning(f"⛔ [Access Denied] Invalid Token request for {user_id}")
        raise HTTPException(status_code=403, detail="Unauthorized access")

    # 2. DB 조회
    user_pii = (
        db.query(models.UserPII).filter(models.UserPII.user_id == user_id).first()
    )

    if not user_pii:
        raise HTTPException(status_code=404, detail="User PII not found")

    logger.info(f"🔓 [Internal API] PII provided for user {user_id} via VPN")
    return user_pii
