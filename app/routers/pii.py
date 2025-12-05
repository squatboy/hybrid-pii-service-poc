from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.core.database import get_db_session
from app.models.pii import UserPII

# 온프레미스에서만 로딩될 라우터
router = APIRouter(prefix="/pii", tags=["PII"])


# 요청 스키마
class TokenizeRequest(BaseModel):
    name: str
    passport_no: str


# 1. 토큰화 (PII 저장)
@router.post("/tokenize")
def tokenize(req: TokenizeRequest, db: Session = Depends(get_db_session)):
    try:
        new_user = UserPII(name=req.name, passport_no=req.passport_no)
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        # ID(토큰)만 반환
        return {"status": "success", "pii_id": new_user.id}
    except Exception as e:
        print(f"❌ [DB Error] {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to store PII: {str(e)}")


# 2. 역토큰화 (PII 조회)
@router.get("/detokenize/{pii_id}")
def detokenize(pii_id: int, db: Session = Depends(get_db_session)):
    try:
        user = db.query(UserPII).filter(UserPII.id == pii_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="PII not found")

        return {"pii_id": user.id, "name": user.name, "passport_no": user.passport_no}
    except Exception as e:
        print(f"❌ [DB Error] {str(e)}")
        raise HTTPException(status_code=500, detail="Database connection error")
