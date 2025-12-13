from pydantic import BaseModel, EmailStr
from typing import Optional


# PII 생성 요청
class PIICreate(BaseModel):
    name: str
    email: EmailStr
    phone: str
    passport_no: str


# PII 응답
class PIIResponse(BaseModel):
    user_id: str
    name: str
    email: EmailStr
    # 보안상 여권번호 등은 마스킹하거나 필요시에만 리턴 (여기선 전체 리턴 가정)
    passport_no: str

    class Config:
        from_attributes = True
