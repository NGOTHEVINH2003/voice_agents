import os
import pytz 
import functools
from datetime import datetime
from google.oauth2 import service_account
from googleapiclient.discovery import build, Resource
from langchain_core.tools import tool
from typing import List, Optional

# Đặt múi giờ (RẤT QUAN TRỌNG cho lịch)
try:
    # Thử lấy từ config nếu có
    from Backend.config import settings
    LOCAL_TIMEZONE = pytz.timezone(settings.TIMEZONE)
except Exception:
    print("Cảnh báo: Không tìm thấy TIMEZONE trong config, dùng 'Asia/Ho_Chi_Minh' làm dự phòng.")
    LOCAL_TIMEZONE = pytz.timezone('Asia/Ho_Chi_Minh') 

class GoogleCalendarService:
    """
    Dịch vụ để tương tác với Google Calendar API sử dụng Service Account.
    """
    def __init__(self, service_account_file: str, calendar_id: str):
        try:
            creds = service_account.Credentials.from_service_account_file(
                service_account_file,
                scopes=['https://www.googleapis.com/auth/calendar']
            )
            self.service: Resource = build('calendar', 'v3', credentials=creds)
            self.calendar_id = calendar_id
            print("GoogleCalendarService initialized successfully.")
        except Exception as e:
            print(f"LỖI: Không thể khởi tạo GoogleCalendarService: {e}")
            print("Hãy chắc chắn tệp service account JSON là chính xác.")
            raise

    def list_events(self, start_time_iso: str, end_time_iso: str) -> str:
        try:
            events_result = self.service.events().list(
                calendarId=self.calendar_id,
                timeMin=start_time_iso,
                timeMax=end_time_iso,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            events = events_result.get('items', [])
            if not events:
                return "Không tìm thấy sự kiện nào trong khoảng thời gian này."
            
            event_list = []
            for event in events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                end = event['end'].get('dateTime', event['end'].get('date'))
                event_list.append(
                    f"- ID: {event['id']}\n"
                    f"  Tóm tắt: {event.get('summary', 'Không có tiêu đề')}\n"
                    f"  Bắt đầu: {start}\n"
                    f"  Kết thúc: {end}\n"
                )
            return "\n".join(event_list)
        except Exception as e:
            return f"Lỗi khi liệt kê sự kiện: {e}"

    def create_event(self, summary: str, start_time_iso: str, end_time_iso: str, description: str = None) -> str:
        try:
            event = {
                'summary': summary,
                'start': {'dateTime': start_time_iso, 'timeZone': str(LOCAL_TIMEZONE)},
                'end': {'dateTime': end_time_iso, 'timeZone': str(LOCAL_TIMEZONE)},
                'description': description,
            }
            created_event = self.service.events().insert(
                calendarId=self.calendar_id,
                body=event
            ).execute()
            return f"Tạo sự kiện thành công. ID sự kiện: {created_event['id']}"
        except Exception as e:
            return f"Lỗi khi tạo sự kiện: {e}"

    def update_event(self, event_id: str, new_summary: str = None, new_start_time_iso: str = None, new_end_time_iso: str = None) -> str:
        try:
            event = self.service.events().get(calendarId=self.calendar_id, eventId=event_id).execute()

            if new_summary:
                event['summary'] = new_summary
            if new_start_time_iso:
                event['start'] = {'dateTime': new_start_time_iso, 'timeZone': str(LOCAL_TIMEZONE)}
            if new_end_time_iso:
                event['end'] = {'dateTime': new_end_time_iso, 'timeZone': str(LOCAL_TIMEZONE)}
            
            updated_event = self.service.events().update(
                calendarId=self.calendar_id,
                eventId=event_id,
                body=event
            ).execute()
            return f"Cập nhật sự kiện '{updated_event.get('summary')}' thành công."
        except Exception as e:
            return f"Lỗi khi cập nhật sự kiện: {e}"

    def delete_event(self, event_id: str) -> str:
        try:
            self.service.events().delete(
                calendarId=self.calendar_id,
                eventId=event_id
            ).execute()
            return f"Xóa sự kiện (ID: {event_id}) thành công."
        except Exception as e:
            return f"Lỗi khi xóa sự kiện: {e}"



def get_calendar_tools(service_instance: GoogleCalendarService) -> List[tool]:
    """
    Gắn các hàm tool (đã có docstring) với các phương thức (logic)
    thực tế của instance 'GoogleCalendarService'.
    """

    # Định nghĩa các tool ngay tại đây.
    # Chúng sẽ "thấy" service_instance thông qua closure.
    
    @tool
    def list_calendar_events(start_time_iso: str, end_time_iso: str) -> str:
        """
        Lists all calendar events between a specific start and end time.
        Use this to check for existing meetings or find free time.
        Args:
            start_time_iso (str): The start time in ISO 8601 format (e.g., '2025-11-05T10:00:00+07:00').
            end_time_iso (str): The end time in ISO 8601 format (e.g., '2025-11-05T18:00:00+07:00').
        """
        return service_instance.list_events(start_time_iso, end_time_iso)

    @tool
    def create_calendar_event(summary: str, start_time_iso: str, end_time_iso: str, description: Optional[str] = None) -> str:
        """
        Creates a new event on the calendar.
        Use this when the user wants to schedule a new meeting or appointment.
        Args:
            summary (str): The title or summary of the event (e.g., 'Team Meeting').
            start_time_iso (str): The start time in ISO 8601 format (e.g., '2025-11-05T10:00:00+07:00').
            end_time_iso (str): The end time in ISO 8601 format (e.g., '2025-11-05T11:00:00+07:00').
            description (str, optional): A description for the event. Defaults to None.
        """
        return service_instance.create_event(summary, start_time_iso, end_time_iso, description)

    @tool
    def update_calendar_event(event_id: str, new_summary: Optional[str] = None, new_start_time_iso: Optional[str] = None, new_end_time_iso: Optional[str] = None) -> str:
        """
        Updates an existing calendar event. Use this to reschedule, rename, or change the duration of a meeting.
        You MUST provide the 'event_id' of the event you want to update.
        Only provide the other fields (summary, start, end) if you want to change them.
        Args:
            event_id (str): The unique ID of the event to update. You must find this using 'list_calendar_events' first.
            new_summary (str, optional): The new title for the event.
            new_start_time_iso (str, optional): The new start time in ISO 8601 format.
            new_end_time_iso (str, optional): The new end time in ISO 8601 format.
        """
        return service_instance.update_event(event_id, new_summary, new_start_time_iso, new_end_time_iso)

    @tool
    def delete_calendar_event(event_id: str) -> str:
        """
        Deletes an event from the calendar. Use this to cancel a meeting.
        You MUST provide the 'event_id' of the event to delete.
        Args:
            event_id (str): The unique ID of the event to delete. You must find this using 'list_calendar_events' first.
        """
        return service_instance.delete_event(event_id)
    
    # Trả về các tool đã được cập nhật
    return [
        list_calendar_events,
        create_calendar_event,
        update_calendar_event,
        delete_calendar_event
    ]

