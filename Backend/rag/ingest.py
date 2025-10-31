from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain.text_splitter import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceBgeEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain_community.vectorstores import FAISS
#from Backend.config import PINECONE_INDEX_NAME, pc
import torch
import os


HEADERS_TO_SPLIT_ON = [
    ("#", "Header1"),
    ("##", "Header2"),
    ("###", "Header3"),
]

PERSIST_DIR = "backend/data/processed/"

def ingest_docs_with_markdown_splitter():
    data_dir = "backend/data/stripe_docs" 
    full_text = ""
    
    for filename in os.listdir(data_dir):
        if filename.endswith(".md"):
            filepath = os.path.join(data_dir, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                full_text += f.read() + "\n\n# NEW DOCUMENT START HERE\n\n"
    
    if not full_text:
        print("❌ Không tìm thấy file .md nào để xử lý.")
        return

    markdown_splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=HEADERS_TO_SPLIT_ON,
        return_each_line=False 
    )

    chunks_with_headers = markdown_splitter.split_text(full_text)
    
    print(f"📄 Split into {len(chunks_with_headers)} chunks using Markdown Headers.")

    final_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000, 
        chunk_overlap=200
    )

    final_chunks = final_splitter.split_documents(chunks_with_headers)
    
    print(f"📦 Final split resulted in {len(final_chunks)} chunks.")
    
    # 4. Tạo Embeddings và Lưu trữ
    embeddings = HuggingFaceBgeEmbeddings(
        model_name="BAAI/bge-base-en-v1.5",
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True}
    )

    print(f"EMBED tạo xong bắt đầu embed vào vector store")

    if os.path.exists(os.path.join(PERSIST_DIR, "index.faiss")):
        print("🧠 Loading existing FAISS index to merge...")
        vectordb = FAISS.load_local(
            PERSIST_DIR, 
            embeddings, 
            allow_dangerous_deserialization=True
        )
    else:
        print("🆕 Creating new FAISS index...")
        vectordb = None

    new_vectordb = FAISS.from_documents(final_chunks, embeddings)

    if vectordb:
        vectordb.merge_from(new_vectordb)
    else:
        vectordb = new_vectordb

    # === Lưu lại index mới ===
    vectordb.save_local(PERSIST_DIR)
    print(f"✅ FAISS index updated and saved at {PERSIST_DIR}")

    print("✅ Ingestion hoàn tất.")


if __name__ == "__main__":
    ingest_docs_with_markdown_splitter()