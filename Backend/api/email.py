from fastapi import APIRouter, HTTPException
from Backend.services.smtp import send_email

router = APIRouter(prefix="/email", tags=["Email"])

@router.post("/send-email")
def sending_email():
    try:
        send_email()

        return {"message": "Email sent successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))