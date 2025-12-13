import logging
import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models import booking as models
from app.schemas import booking as schemas
from app.core.config import settings

logger = logging.getLogger("uvicorn")

router = APIRouter(prefix="/bookings", tags=["Bookings (Cloud)"])


# -----------------------------------------------------------------------------
# 1. 예약 생성 (퍼블릭 데이터만 Aurora에 저장)
# -----------------------------------------------------------------------------
@router.post("/", response_model=schemas.BookingResponse)
def create_booking(booking_in: schemas.BookingCreate, db: Session = Depends(get_db)):
    db_booking = models.Booking(
        user_id=booking_in.user_id,
        departure_date=booking_in.departure_date,
        arrival_date=booking_in.arrival_date,
        destination=booking_in.destination,
        status="PENDING",
    )
    db.add(db_booking)
    db.commit()
    db.refresh(db_booking)

    logger.info(
        f"📅 [Booking] Created booking {db_booking.booking_id} for user {booking_in.user_id}"
    )
    return db_booking


# -----------------------------------------------------------------------------
# 2. 예약 확정 (Data Aggregation & Mock Execution)
# -----------------------------------------------------------------------------
@router.post("/{booking_id}/confirm", response_model=schemas.BookingResponse)
async def confirm_booking(booking_id: int, db: Session = Depends(get_db)):
    # A. 예약 정보 조회 (Aurora)
    booking = (
        db.query(models.Booking).filter(models.Booking.booking_id == booking_id).first()
    )
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    if booking.status == "CONFIRMED":
        return booking

    # B. PII 조회 (온프레미스 API 호출 via VPN)
    onprem_url = getattr(settings, "ONPREM_SERVICE_URL", "http://10.10.10.20:8000")
    token = getattr(settings, "INTERNAL_API_TOKEN", "my-secret-token")

    logger.info(
        f"🔗 [Integration] Fetching PII from {onprem_url} for user {booking.user_id}..."
    )

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(
                f"{onprem_url}/pii/internal/{booking.user_id}",
                headers={"x-internal-token": token},
            )

            if response.status_code != 200:
                logger.error(
                    f"❌ [On-Prem Error] Status: {response.status_code}, Body: {response.text}"
                )
                raise HTTPException(
                    status_code=502, detail="Failed to fetch PII from On-Premise"
                )

            pii_data = response.json()

    except httpx.RequestError as exc:
        logger.error(f"❌ [Network Error] Could not connect to On-Premise: {exc}")
        raise HTTPException(status_code=503, detail="On-Premise service unavailable")

    # C. Mock Business Logic (여권번호 + 일정으로 예약 수행)
    passport = pii_data.get("passport_no", "UNKNOWN")
    user_name = pii_data.get("name", "UNKNOWN")

    print("=" * 60)
    print(f"✈️  [MOCK EXECUTION] Processing Booking #{booking_id}")
    print(f"    - User: {user_name} (Passport: {passport})")
    print(f"    - Destination: {booking.destination}")
    print(f"    - Date: {booking.departure_date} ~ {booking.arrival_date}")
    print(f"    -> Sending request to Airline/Hotel Vendor API... SUCCESS")
    print("=" * 60)

    # D. 상태 업데이트 (Aurora)
    booking.status = "CONFIRMED"
    booking.hotel_name = f"Hilton {booking.destination} (Auto-Assigned)"

    db.commit()
    db.refresh(booking)

    logger.info(f"✅ [Booking] Confirmed booking #{booking_id}")
    return booking
