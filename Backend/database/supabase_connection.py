from supabase import create_client, Client
import os

SUPABASE_URL = "https://yootkntbhhlhcootrrij.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inlvb3RrbnRiaGhsaGNvb3RycmlqIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjIzNTUyMTcsImV4cCI6MjA3NzkzMTIxN30.f4rMtQa2C8YqRVnxrnd8jpoE6H1ZDO-S9xFQuI1_khE"

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Thiếu SUPABASE_URL hoặc SUPABASE_KEY trong file .env")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

print("✅ Supabase client initialized thành công")
