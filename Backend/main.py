from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from Backend.api import ingest, chat, ws_voice

app = FastAPI(title="AI Business Assistant - Advanced RAG (FAISS)")

app.add_middleware(
    CORSMiddleware,
    allow_origins = ["*"],
    allow_methods = ["*"],
    allow_credentials = True,
    allow_headers = ["*"],
)

app.include_router(ingest.router)
app.include_router(chat.router)
app.include_router(ws_voice.router)


@app.get("/")
def root():
    return RedirectResponse(url="/docs")
