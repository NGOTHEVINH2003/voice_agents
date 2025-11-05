import os
from pathlib import Path
from typing import List, Dict
from langchain.docstore.document import Document
from langchain_community.document_loaders import TextLoader, PyPDFLoader, UnstructuredHTMLLoader
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from Backend.utils.splitter import chunk_texts
from Backend.config import settings
import pickle

EMBED_MODEL = settings.EMBEDDING_MODEL
INDEX_DIR = settings.FAISS_INDEX_DIR

# Helper: load a file and return list[str] raw texts
def load_file_to_texts(path: Path) -> List[Dict]:
    path = Path(path)
    ext = path.suffix.lower()
    if ext in [".txt", ".md"]:
        loader = TextLoader(str(path), encoding="utf-8")
    elif ext in [".pdf"]:
        loader = PyPDFLoader(str(path))
    elif ext in [".html", ".htm"]:
        loader = UnstructuredHTMLLoader(str(path))
    else:
        loader = TextLoader(str(path), encoding="utf-8")
    docs = loader.load()

    return docs

def ingest_documents_from_paths(paths: List[str], namespace: str = ""):
    """
    paths: list of file paths (local)
    namespace: optional label (used if storing multiple indexes)
    """
    all_docs = []
    for p in paths:
        docs = load_file_to_texts(Path(p))
        for d in docs:
            all_docs.append(Document(page_content=d.page_content, metadata={"source": str(p), **(d.metadata or {})}))

    chunked_docs = []
    for d in all_docs:
        chunks = chunk_texts([d.page_content])
        for i, c in enumerate(chunks):
            md = dict(d.metadata)
            md.update({"chunk": i})
            chunked_docs.append(Document(page_content=c, metadata=md))

    embedder = HuggingFaceEmbeddings(model_name=EMBED_MODEL)
    index_path = INDEX_DIR / f"{namespace}"
    index_path.mkdir(parents=True, exist_ok=True)

    if (index_path / "index.faiss").exists():
        print("[yellow]Loading existing FAISS and adding documents...[/yellow]")
        vectordb = FAISS.load_local(str(index_path), embedder)
        vectordb.add_documents(chunked_docs)
        vectordb.save_local(str(index_path))
    else:
        print("[green]Creating new FAISS index...[/green]")
        vectordb = FAISS.from_documents(chunked_docs, embedder)
        vectordb.save_local(str(index_path))  # lưu index


    # Also persist metadata mapping if needed (FAISS wrapper handles metadata in LangChain)
    print(f"[green]Ingested {len(chunked_docs)} chunks into FAISS at {index_path}[/green]")
    return True
