import os
from pathlib import Path
from typing import List, Dict
from langchain.docstore.document import Document
from langchain_community.document_loaders import TextLoader, PyPDFLoader, UnstructuredHTMLLoader
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from Backend.utils.splitter import chunk_texts
from Backend.config import settings

EMBED_MODEL = settings.EMBEDDING_MODEL
INDEX_DIR = Path(settings.FAISS_INDEX_DIR)

# Helper: load a file and return list[Document]
def load_file_to_texts(path: Path) -> List[Document]:
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

def ingest_documents_from_paths(paths: List[str]):
    """
    paths: list of file paths (local)
    Tất cả documents sẽ được lưu vào 1 FAISS index duy nhất
    """
    # Load tất cả documents
    all_docs = []
    for p in paths:
        try:
            docs = load_file_to_texts(Path(p))
            for d in docs:
                all_docs.append(Document(
                    page_content=d.page_content, 
                    metadata={"source": str(p), **(d.metadata or {})}
                ))
            print(f"✓ Loaded: {p}")
        except Exception as e:
            print(f"✗ Error loading {p}: {e}")

    if not all_docs:
        print("No documents loaded!")
        return False

    # Chunk tất cả documents
    chunked_docs = []
    for d in all_docs:
        chunks = chunk_texts([d.page_content])
        for i, c in enumerate(chunks):
            md = dict(d.metadata)
            md.update({"chunk": i})
            chunked_docs.append(Document(page_content=c, metadata=md))

    print(f"Total chunks: {len(chunked_docs)}")

    # Tạo embeddings
    embedder = HuggingFaceEmbeddings(model_name=EMBED_MODEL)
    
    # Tạo thư mục nếu chưa có
    INDEX_DIR.mkdir(parents=True, exist_ok=True)

    # Kiểm tra nếu đã có index cũ
    if (INDEX_DIR / "index.faiss").exists():
        print("Loading existing FAISS index and adding new documents...")
        vectordb = FAISS.load_local(
            str(INDEX_DIR), 
            embedder,
            allow_dangerous_deserialization=True
        )
        vectordb.add_documents(chunked_docs)
        print(f"✓ Added {len(chunked_docs)} chunks to existing index")
    else:
        print("Creating new FAISS index...")
        vectordb = FAISS.from_documents(chunked_docs, embedder)
        print(f"✓ Created new index with {len(chunked_docs)} chunks")

    # Lưu index
    vectordb.save_local(str(INDEX_DIR))
    print(f"✓ FAISS index saved to: {INDEX_DIR}")
    
    return True