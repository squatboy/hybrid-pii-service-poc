from sqlalchemy import Column, Integer, String, DateTime, func
from app.core.database import Base


class Booking(Base):
    __tablename__ = "bookings"

    booking_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(36), nullable=False, index=True)  # user_pii.user_id와 매핑

    # 출장 일정 정보
    departure_date = Column(String(10), nullable=False)  # YYYY-MM-DD
    arrival_date = Column(String(10), nullable=False)  # YYYY-MM-DD
    destination = Column(String(100), nullable=False)

    # 자동 배정 결과
    hotel_name = Column(String(100), nullable=True)  # 예약 확정 시 기입

    # 상태 관리 (PENDING, CONFIRMED, FAILED)
    status = Column(String(20), default="PENDING")

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
