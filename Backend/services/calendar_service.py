import os
import pytz 
import functools
from datetime import datetime
from google.oauth2 import service_account
from googleapiclient.discovery import build, Resource
from langchain_core.tools import tool
from typing import List, Optional

try:
    from Backend.config import settings
    LOCAL_TIMEZONE = pytz.timezone(settings.TIMEZONE)
except Exception:
    print("Warning: TIMEZONE NOT FOUND IN config, USING 'Asia/Ho_Chi_Minh' AS BACKUP.")
    LOCAL_TIMEZONE = pytz.timezone('Asia/Ho_Chi_Minh') 

class GoogleCalendarService:
    """
    Service for interacting with google calendar api using google serivce account.
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
            print(f"Error: Cannot initialzied GoogleCalendarService: {e}")
            print(" Please ensure that the service account json is correct.")
            raise

    def list_events(self, start_time_iso: str, end_time_iso: str) -> str:
        try:
            start_dt = datetime.fromisoformat(start_time_iso.replace('Z', '+00:00'))
            end_dt = datetime.fromisoformat(end_time_iso.replace('Z', '+00:00'))
            

            if start_dt.tzinfo is None:
                start_dt = LOCAL_TIMEZONE.localize(start_dt)
            if end_dt.tzinfo is None:
                end_dt = LOCAL_TIMEZONE.localize(end_dt)
            
            start_time_with_tz = start_dt.isoformat()
            end_time_with_tz = end_dt.isoformat()

            events_result = self.service.events().list(
                calendarId=self.calendar_id,
                timeMin=start_time_with_tz,
                timeMax=end_time_with_tz,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            events = events_result.get('items', [])
            if not events:
                return "No events found in this time window."
            
            event_list = []
            for event in events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                end = event['end'].get('dateTime', event['end'].get('date'))
                event_list.append(
                    f"- ID: {event['id']}\n"
                    f"  SUMMARY: {event.get('summary', 'Not title')}\n"
                    f"  Start TIME: {start}\n"
                    f"  END TIME: {end}\n"
                )
            return "\n".join(event_list)
        except Exception as e:
            return f"error when listing events: {e}"

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
            return f"Successfully create events. Event ID: {created_event['id']}"
        except Exception as e:
            return f"Errors occur when create event: {e}"

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
            return f"Update Event '{updated_event.get('summary')}' Successfully."
        except Exception as e:
            return f"Error when Update Event: {e}"

    def delete_event(self, event_id: str) -> str:
        try:
            self.service.events().delete(
                calendarId=self.calendar_id,
                eventId=event_id
            ).execute()
            return f"Delete Event (ID: {event_id}) Successfully."
        except Exception as e:
            return f"Error when Delete Event: {e}"



def get_calendar_tools(service_instance: GoogleCalendarService) -> List[tool]:
   
    @tool
    def list_calendar_events(start_time_iso: str, end_time_iso: str) -> str:
        """
        Lists all calendar events between a specific start and end time. if start time and end time is not specify automatically understand it from  0 am - 12pm
        if user only list start time you can search with end time is one hour duration. 
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
       IMPORTANT: The user will NOT provide the 'event_id'. They will describe the event (e.g., "reschedule my 3 PM meeting tomorrow to 4 PM").
        
        Your workflow MUST be:
        1. Use 'list_calendar_events' with the timeframe the user provided (e.g., 'tomorrow 3 PM') to FIND the event.
        2. Get the 'event_id' from the search results.
        3. Call this 'update_calendar_event' tool with the 'event_id' you found and the new details (e.g., 'new_start_time_iso'='2025-11-05T16:00:00+07:00').
        
        Error Handling: If you find more than 1 matching event, you MUST ASK the user for clarification before updating.

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

       IMPORTANT: The user will NOT provide the 'event_id'. They will describe the event (e.g., "cancel my 10 AM meeting today").
        
        Your workflow MUST be:
        1. Use 'list_calendar_events' with the timeframe the user provided to FIND the event.
        2. Get the 'event_id' from the search results.
        3. Call this 'delete_calendar_event' tool with the 'event_id' you found.
        
        Error Handling: If you find more than 1 matching event, you MUST ASK the user for clarification before deleting.
        
        Args:
            event_id (str): The unique ID of the event to delete. You must find this using 'list_calendar_events' first.
        """
        return service_instance.delete_event(event_id)
    
    return [
        list_calendar_events,
        create_calendar_event,
        update_calendar_event,
        delete_calendar_event
    ]

