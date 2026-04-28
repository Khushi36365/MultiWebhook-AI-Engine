from fastapi import APIRouter
from services.email_service import send_email

router = APIRouter()

@router.post("/send-email")
def send_email_api(data: dict):
    return send_email(
        to=data.get("to"),
        subject=data.get("subject"),
        body=data.get("body")
    )