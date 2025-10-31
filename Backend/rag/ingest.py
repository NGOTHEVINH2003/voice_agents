import os
from pathlib import Path
from typing import List, Dict
from langchain.docstore.document import Document
from langchain.document_loaders import TextLoader, PyPDFLoader, UnstructuredHTMLLoader
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import FAISS
from Backend.utils.splitter import chunk_texts
from Backend.config import settings
from rich import print
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
        # fallback to text loader
        loader = TextLoader(str(path), encoding="utf-8")
    docs = loader.load()
    # docs are LangChain Document objects
    return docs

def ingest_documents_from_paths(paths: List[str], namespace: str = "default"):
    """
    paths: list of file paths (local)
    namespace: optional label (used if storing multiple indexes)
    """
    all_docs = []
    for p in paths:
        docs = load_file_to_texts(Path(p))
        for d in docs:
            # preserve metadata like source
            all_docs.append(Document(page_content=d.page_content, metadata={"source": str(p), **(d.metadata or {})}))

    # chunk content
    chunked_docs = []
    for d in all_docs:
        chunks = chunk_texts([d.page_content])
        for i, c in enumerate(chunks):
            md = dict(d.metadata)
            md.update({"chunk": i})
            chunked_docs.append(Document(page_content=c, metadata=md))

    # create embeddings and FAISS index (or load existing and add)
    embedder = HuggingFaceEmbeddings(model_name=EMBED_MODEL)  # may require HF token/config
    index_path = INDEX_DIR / f"{namespace}_faiss"
    index_path.mkdir(parents=True, exist_ok=True)

    if (index_path / "index.faiss").exists():
        print("[yellow]Loading existing FAISS and adding documents...[/yellow]")
        vectordb = FAISS.load_local(str(index_path), embedder)
        vectordb.add_documents(chunked_docs)
    else:
        print("[green]Creating new FAISS index...[/green]")
        vectordb = FAISS.from_documents(chunked_docs, embedder, index_path=str(index_path))

    # Also persist metadata mapping if needed (FAISS wrapper handles metadata in LangChain)
    print(f"[green]Ingested {len(chunked_docs)} chunks into FAISS at {index_path}[/green]")
    return True
