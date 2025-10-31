from langchain.text_splitter import RecursiveCharacterTextSplitter
from Backend.config import settings

def chunk_texts(texts):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.CHUNK_SIZE,
        chunk_overlap=settings.CHUNK_OVERLAP
    )
    docs = []
    for t in texts:
        chunks = splitter.split_text(t)
        docs.extend(chunks)
    return docs
