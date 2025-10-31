from get_service import get_calendar_service

service = get_calendar_service()

def create_event(template: dict):
    try:
        response = service.events().insert(calendarId="primary", body=template).execute()
        return response
    except Exception as e:
        return str(e)
    
def get_event(eventId: str):
    try:
        response = service.events().get(calendarId="primary", eventId=eventId).execute()
        return response
    except Exception as e:
        return str(e)

def delete_event(eventId: str):
    try:
        response = service.events().delete(calendarId="primary", eventId=eventId).execute()
        return response
    except Exception as e:
        return str(e)
    
def update_event(eventId: str, template: dict):
    try:
        response = service.events().insert(calendarId="primary", eventId=eventId, body=template).execute()
        return response
    except Exception as e:
        return str(e)