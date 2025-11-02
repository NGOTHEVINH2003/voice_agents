from fastapi import APIRouter, UploadFile, File, HTTPException
from Backend.services.whisper_service import transcribe_audio
from Backend.services.nlu_service import parse_meeting_request
from Backend.calendar.calendar_crud import create_event
import tempfile, os
from datetime import datetime, timedelta

router = APIRouter(prefix="/voice", tags=["Voice"])

def _prepare_google_event_data(parsed_data: dict):
    """
    Hàm nội bộ để chuyển đổi dict từ NLU
    thành format chuẩn của Google Calendar API.
    """
    try:
        start_time_str = parsed_data["start"]
        duration = parsed_data.get("duration_hour", 1) # Mặc định 1 giờ

        # Chuyển string ISO format về đối tượng datetime
        start_time_dt = datetime.fromisoformat(start_time_str)
        
        # Tính toán thời gian kết thúc
        end_time_dt = start_time_dt + timedelta(hours=duration)

        # Tạo template sự kiện chuẩn của Google API
        event_template = {
            'summary': parsed_data["summary"],
            'description': parsed_data["description"],
            'start': {
                'dateTime': start_time_dt.isoformat(),
                'timeZone': 'Asia/Ho_Chi_Minh', # (Luôn set timezone)
            },
            'end': {
                'dateTime': end_time_dt.isoformat(),
                'timeZone': 'Asia/Ho_Chi_Minh',
            },
        }
        return event_template
    except Exception as e:
        print(f"Lỗi khi chuẩn bị dữ liệu sự kiện: {e}")
        return None

@router.post("/schedule_from_audio")
async def schedule_from_audio(file: UploadFile = File(...)):
    temp_dir = tempfile.gettempdir()
    temp_path = os.path.join(temp_dir, file.filename)

    with open(temp_path, "wb") as f:
        f.write(await file.read())

    text = transcribe_audio(temp_path)
    os.remove(temp_path)

    data = parse_meeting_request(text)

    if not data:
        return {"transcript": text, 
                "message": "Đã nhận dạng văn bản, nhưng không phát hiện yêu cầu đặt lịch (hoặc lỗi trích xuất NLU)."}
    
    if data["intent"] != "schedule_meeting":
         return {"transcript": text, 
                "message": f"Phát hiện ý định: {data['intent']}, không phải đặt lịch."}
    
    event_body = _prepare_google_event_data(data)

    if not event_body:
        raise HTTPException(
            status_code=400, 
            detail=f"Lỗi xử lý dữ liệu NLU (có thể do lỗi định dạng thời gian: {data.get('start')})"
        )
    
    try:
        event_response = create_event(event_body) # <-- GỌI GOOGLE API
        
        link = event_response.get('htmlLink')
        event_id = event_response.get('id')

        # --- BƯỚC 5: TRẢ VỀ KẾT QUẢ THÀNH CÔNG ---
        return {
            "transcript": text,
            "message": "✅ Đã tạo lịch thành công!",
            "google_calendar_link": link,
            "event_id": event_id,
            "nlu_data": data
        }
    except Exception as e:
        # Xử lý nếu Google API bị lỗi
        raise HTTPException(
            status_code=500, 
            detail=f"Lỗi khi gọi Google Calendar API: {e}"
        )