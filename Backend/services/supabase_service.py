from Backend.database.supabase_connection import supabase
from Backend.database import models

class SupabaseService:
    def __init__(self):
        self.client = supabase

    # ---------------- USERS ----------------
    def create_user(self, user: models.User):
        return self.client.table("user").insert(user.dict()).execute()

    def get_user_by_email(self, email: str):
        return self.client.table("user").select("*").eq("email", email).execute()

    # ---------------- SESSIONS ----------------
    def create_session(self, session: models.Session):
        return self.client.table("session").insert(session.dict()).execute()

    def get_sessions_by_user(self, user_id: str):
        return self.client.table("session").select("*").eq("user_id", user_id).execute()

    # ---------------- MESSAGES ----------------
    def add_message(self, message: models.Message):
        return self.client.table("message").insert(message.dict()).execute()

    def get_messages(self, session_id: str):
        return self.client.table("message").select("*").eq("session_id", session_id).execute()

    # ---------------- DOCUMENTS ----------------
    def add_document(self, document: models.Document):
        return self.client.table("document").insert(document.dict()).execute()

    def get_documents(self, user_id: str):
        return self.client.table("document").select("*").eq("user_id", user_id).execute()

    # ---------------- AUTOMATION RUNS ----------------
    def add_automation_run(self, run: models.AutomationRun):
        return self.client.table("automation_run").insert(run.dict()).execute()

    def get_automation_runs(self, user_id: str):
        return self.client.table("automation_run").select("*").eq("user_id", user_id).execute()
