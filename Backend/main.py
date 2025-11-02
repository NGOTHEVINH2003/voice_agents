from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from Backend.api import ingest, chat, voice, email

app = FastAPI(title="AI Business Assistant - Advanced RAG (FAISS)")


origins = [
    "http://localhost",
    "http://localhost:3000",  # Nếu FE của bạn chạy trên cổng 3000
    "http://localhost:5173",  # Nếu bạn dùng Vite (cổng mặc định)
    "http://127.0.0.1:5500", # Thêm cả 127.0.0.1
    "http://127.0.0.1:5173",
    # "https://your-production-domain.com" # Thêm domain production của bạn
]
app.add_middleware(
    CORSMiddleware,
    allow_origins = origins,
    allow_methods = ["*"],
    allow_headers = ["*"],
)

app.include_router(ingest.router)
app.include_router(chat.router)

app.include_router(voice.router)

app.include_router(email.router)

@app.get("/")
def root():
    return RedirectResponse(url="/docs")
