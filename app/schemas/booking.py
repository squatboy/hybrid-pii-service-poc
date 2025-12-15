from pydantic import BaseModel
from typing import Optional


# 예약 생성 요청
class BookingCreate(BaseModel):
    user_id: str
    departure_date: str
    arrival_date: str
    destination: str


# 예약 확정 요청
class BookingConfirm(BaseModel):
    pass  # 별도 입력 없이 ID로만 확정하거나, 추가 옵션 가능


# 예약 정보 응답
class BookingResponse(BaseModel):
    booking_id: int
    user_id: str
    destination: str
    status: str
    hotel_name: Optional[str] = None

    class Config:
        from_attributes = True


# 실시간 견적 산출 응답
class QuoteResponse(BaseModel):
    user_id: str
    destination: str
    estimated_price: float
    quote_token: str
    valid_until: str


# [통합] 전체 예약 상세 (PII 포함 - 관리자/본인용)
class FullBookingDetails(BookingResponse):
    user_name: str
    passport_no: str
