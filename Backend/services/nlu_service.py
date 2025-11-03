from transformers import pipeline
import json, os, re
from datetime import datetime
import dateparser
from dateparser.search import search_dates

# === NLU ===
classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")

def classify(text: str):
    labels = ["schedule_meeting", "check_schedule", "cancel_meeting", "update_meeting"]
    result = classifier(text, labels)
    return {
        "intent": result["labels"][0],
        "confidence": result["scores"][0]
    }

# === Summary Extract ===
def extract_summary(text: str):
    patterns = [
        r"họp với ([\w\s]+)",
        r"trao đổi với ([\w\s]+)",
        r"gặp ([\w\s]+)",
        r"cuộc họp với ([\w\s]+)",
        r"meeting with ([\w\s]+)",
        r"call with ([\w\s]+)",
        r"talk to ([\w\s]+)"
    ]
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return f"Cuộc họp với {match.group(1).strip()}"
    return "Cuộc họp không tiêu đề"

# === Parse Meeting Request ===
def parse_meeting_request(text: str):
    result = classify(text)
    intent = result["intent"]

    if intent != "schedule_meeting":
        print("Intent không phải là đặt lịch.")
        return None

    print(f"Câu gốc: '{text}'")
    
    # Dùng dateparser.search để tìm ngày tháng trong cả câu
    # Nó sẽ trả về một list các tuple (chuỗi_tìm_thấy, datetime_obj)
    date_results = search_dates(
        text, 
        languages=['en', 'vi'], # Ưu tiên tiếng Anh cho 'p.m.'
        settings={
            'PREFER_DATES_FROM': 'future',  # Luôn ưu tiên thời gian trong tương lai
            'TIMEZONE': 'Asia/Ho_Chi_Minh' # Đặt múi giờ cho kết quả
        }
    )
    
    dt = None
    if date_results:
        # Lấy kết quả đầu tiên tìm được
        found_string, dt_obj = date_results[0]
        print(f"Cụm từ thời gian tìm thấy: '{found_string}'")
        print(f"Kết quả datetime (đã có múi giờ): {dt_obj}")
        dt = dt_obj # Đây là datetime object (đã có timezone)
    
    if not dt:
        print("Không thể phân tích thời gian từ câu. Dùng thời gian hiện tại (fallback).")
        dt = datetime.now() 

    summary = extract_summary(text)

    data = {
        "intent": intent,
        "confidence": result["confidence"],
        "summary": summary,
        "description": text,
        "start": dt.isoformat(),
        "duration_hour": 1,
        "status": "pending"
    }

    print(f"✅ NLU đã xử lý: {summary} lúc {dt.isoformat()}")
    return data # Trả về dictionary 'data'
