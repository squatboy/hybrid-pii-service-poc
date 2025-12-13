import uuid
from sqlalchemy import Column, String, DateTime, func
from app.core.database import Base


class UserPII(Base):
    __tablename__ = "user_pii"

    # UUID를 PK로 사용 (두 DB 간의 연결 고리)
    user_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    # 암호화되어 저장될 필드들
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False, index=True)
    phone = Column(String(255), nullable=False)
    passport_no = Column(String(255), nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
