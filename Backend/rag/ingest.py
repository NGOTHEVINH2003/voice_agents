from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain.text_splitter import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceBgeEmbeddings
from langchain_pinecone import PineconeVectorStore
from Backend.config import PINECONE_INDEX_NAME, pc
import torch
import os

# Định nghĩa các tiêu đề Markdown mà bạn muốn dùng để chia tài liệu.
# Tài liệu Stripe của bạn dùng các tiêu đề từ ## đến ####
# Ta sẽ dùng ## và ### làm điểm chia chính.
HEADERS_TO_SPLIT_ON = [
    ("#", "Header1"),
    ("##", "Header2"),
    ("###", "Header3"),
]

def ingest_docs_with_markdown_splitter():
    # 1. Tải toàn bộ nội dung text từ tất cả các file .md
    # Vì MarkdownHeaderTextSplitter cần text, ta cần đọc file thủ công
    
    # Giả định thư mục chứa file là "backend/data"
    data_dir = "backend/data/stripe_docs" 
    full_text = ""
    
    # Kết hợp nội dung của tất cả các file thành một chuỗi lớn
    for filename in os.listdir(data_dir):
        if filename.endswith(".md"):
            filepath = os.path.join(data_dir, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                # Thêm dấu phân cách rõ ràng giữa các tài liệu.
                # Đây là bước quan trọng để tránh lẫn lộn giữa các file.
                full_text += f.read() + "\n\n# NEW DOCUMENT START HERE\n\n"
    
    if not full_text:
        print("❌ Không tìm thấy file .md nào để xử lý.")
        return

    # 2. Chia tài liệu dựa trên cấu trúc Markdown Headers
    # Bước này sẽ giữ nguyên vẹn các bảng, đoạn code giữa các tiêu đề.
    markdown_splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=HEADERS_TO_SPLIT_ON,
        # Giữ lại cả các tiêu đề đã dùng để chia trong metadata của chunk
        return_each_line=False 
    )
    
    # Chia chuỗi văn bản lớn thành các Document (chunks)
    # Lưu ý: Lúc này các chunks là Document objects của LangChain
    chunks_with_headers = markdown_splitter.split_text(full_text)
    
    print(f"📄 Split into {len(chunks_with_headers)} chunks using Markdown Headers.")

    # 3. Chia nhỏ các chunks còn lại (nếu quá lớn)
    # Vì MarkdownHeaderTextSplitter không giới hạn kích thước, ta cần thêm 
    # RecursiveCharacterTextSplitter để xử lý các đoạn quá dài (ví dụ, đoạn văn bản
    # dài giữa hai tiêu đề).
    
    # Ta sẽ dùng RecursiveCharacterTextSplitter để chia lại các chunks quá dài
    # Nếu một chunk đã ngắn, nó sẽ không bị chia nữa.
    final_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000, 
        chunk_overlap=200
    )

    final_chunks = final_splitter.split_documents(chunks_with_headers)
    
    print(f"📦 Final split resulted in {len(final_chunks)} chunks.")
    
    # 4. Tạo Embeddings và Lưu trữ
    embeddings = HuggingFaceBgeEmbeddings(
        model_name="BAAI/bge-base-en-v1.5",
        model_kwargs={"device": "cuda" if torch.cuda.is_available() else "cpu"},
        encode_kwargs={"normalize_embeddings": True}
    )

    # Khởi tạo hoặc kết nối với Pinecone
    # index = pc.Index(PINECONE_INDEX_NAME) # Dòng này không cần thiết khi dùng from_documents
    
    vectorstore = PineconeVectorStore.from_documents(
        documents=final_chunks,
        embedding=embeddings,
        index_name=PINECONE_INDEX_NAME # Đổi từ 'index' sang 'index_name' cho rõ ràng
    )
    
    print("✅ Ingestion hoàn tất.")


if __name__ == "__main__":
    ingest_docs_with_markdown_splitter()