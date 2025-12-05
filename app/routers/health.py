from fastapi import APIRouter
import socket
from app.core.config import settings

router = APIRouter()


@router.get("/health")
def health_check():
    return {
        "status": "ok",
        "hostname": socket.gethostname(),
        "mode": "on-premise" if settings.IS_ONPREM else "cloud",
    }
