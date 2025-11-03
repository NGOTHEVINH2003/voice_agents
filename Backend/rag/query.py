from langchain.chains.retrieval_qa.base import RetrievalQA
from langchain_community.embeddings import HuggingFaceBgeEmbeddings
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.vectorstores import FAISS
from langchain.prompts import PromptTemplate
from Backend.config import settings
import time
import numpy as np
from typing import Dict, List, Any

index_path = settings.FAISS_INDEX_DIR
EMBED_MODEL = settings.EMBEDDING_MODEL
GOOGLE_API_TOKEN = settings.GOOGLE_API_KEY
TOP_K = settings.TOP_K
LLM_MODEL = settings.LLM_MODEL


def calculate_retrieval_metrics(retrieved_docs: List[Any], query: str) -> Dict[str, Any]:
    """
    Tính toán các metrics cho retrieval quality
    """
    if not retrieved_docs:
        return {
            "num_documents": 0,
            "avg_similarity_score": 0.0,
            "max_similarity_score": 0.0,
            "min_similarity_score": 0.0,
            "score_distribution": []
        }
    
    # Lấy similarity scores từ metadata nếu có
    scores = []
    for doc in retrieved_docs:
        if hasattr(doc, 'metadata') and 'score' in doc.metadata:
            scores.append(doc.metadata['score'])
    
    metrics = {
        "num_documents": len(retrieved_docs),
        "avg_document_length": np.mean([len(doc.page_content) for doc in retrieved_docs]),
        "total_context_length": sum([len(doc.page_content) for doc in retrieved_docs])
    }
    
    if scores:
        metrics.update({
            "avg_similarity_score": float(np.mean(scores)),
            "max_similarity_score": float(np.max(scores)),
            "min_similarity_score": float(np.min(scores)),
            "score_std": float(np.std(scores)),
            "score_distribution": scores
        })
    
    return metrics


def calculate_confidence(answer: str, retrieved_docs: List[Any], query: str) -> Dict[str, Any]:
    """
    Tính toán confidence score dựa trên nhiều yếu tố
    """
    confidence_score = 0.0
    factors = {}
    
    # Factor 1: Độ dài câu trả lời (câu trả lời dài thường có nhiều thông tin hơn)
    answer_length = len(answer)
    if answer_length > 50:
        length_score = min(1.0, answer_length / 500)
    else:
        length_score = 0.3
    factors["answer_length_score"] = length_score
    
    # Factor 2: Kiểm tra "I don't know" hoặc các câu trả lời không chắc chắn
    uncertain_phrases = ["i don't know", "not sure", "unclear", "cannot determine", "no information"]
    is_uncertain = any(phrase in answer.lower() for phrase in uncertain_phrases)
    certainty_score = 0.2 if is_uncertain else 0.9
    factors["certainty_score"] = certainty_score
    
    # Factor 3: Số lượng documents retrieved
    doc_count_score = min(1.0, len(retrieved_docs) / TOP_K)
    factors["document_coverage_score"] = doc_count_score
    
    # Factor 4: Similarity scores nếu có
    if retrieved_docs and hasattr(retrieved_docs[0], 'metadata') and 'score' in retrieved_docs[0].metadata:
        scores = [doc.metadata['score'] for doc in retrieved_docs if 'score' in doc.metadata]
        if scores:
            similarity_score = np.mean(scores)
            factors["avg_similarity_score"] = float(similarity_score)
        else:
            similarity_score = 0.5
            factors["avg_similarity_score"] = 0.5
    else:
        similarity_score = 0.5
        factors["avg_similarity_score"] = 0.5
    
    # Tính confidence tổng hợp (weighted average)
    confidence_score = (
        0.2 * length_score +
        0.4 * certainty_score +
        0.2 * doc_count_score +
        0.2 * similarity_score
    )
    
    return {
        "confidence_score": float(confidence_score),
        "confidence_level": "high" if confidence_score > 0.7 else "medium" if confidence_score > 0.4 else "low",
        "factors": factors
    }


def get_rag_chain():
    embeddings = HuggingFaceBgeEmbeddings(
        model_name=EMBED_MODEL,
        encode_kwargs={"normalize_embeddings": True}
    )
    vectorstore = FAISS.load_local(index_path, embeddings, allow_dangerous_deserialization=True)

    retriever = vectorstore.as_retriever(search_kwargs={"k": TOP_K})

    llm = ChatGoogleGenerativeAI(
        model=LLM_MODEL,
        google_api_key=GOOGLE_API_TOKEN,
        temperature=0.2
    )

    prompt_template = PromptTemplate(
        input_variables=["context", "question"],
        template=(
            "You are an AI assistant that answers questions based on retrieved data.\n"
            "Use the following context to answer the question.\n"
            "If the user does not specify the part, answer all to your knowledge from the context.\n"
            "If you don't know, reply 'I don't know'.\n\n"
            "Context:\n{context}\n\nQuestion: {question}"
        ),
    )

    chain = RetrievalQA.from_chain_type(
        llm=llm,
        retriever=retriever,
        return_source_documents=True,
        chain_type_kwargs={"prompt": prompt_template},
        chain_type="stuff"
    )

    return chain


def query_with_metrics(question: str) -> Dict[str, Any]:
    """
    Thực hiện query và trả về kết quả kèm theo các metrics
    """
    # Bắt đầu đo thời gian tổng
    start_time = time.time()
    
    # Lấy chain
    chain_init_start = time.time()
    chain = get_rag_chain()
    chain_init_time = time.time() - chain_init_start
    
    # Thực hiện query
    query_start = time.time()
    result = chain({"query": question})
    query_time = time.time() - query_start
    
    # Tổng thời gian
    total_time = time.time() - start_time
    
    # Lấy thông tin từ result
    answer = result.get("result", "")
    source_docs = result.get("source_documents", [])
    
    # Tính toán các metrics
    retrieval_metrics = calculate_retrieval_metrics(source_docs, question)
    confidence_metrics = calculate_confidence(answer, source_docs, question)
    
    # Tổng hợp kết quả
    return {
        "answer": answer,
        "retrieval_quality": {
            "documents_retrieved": retrieval_metrics["num_documents"],
            "avg_document_length": retrieval_metrics.get("avg_document_length", 0),
            "total_context_length": retrieval_metrics.get("total_context_length", 0)
        },
        "retrieval_metrics": retrieval_metrics,
        "confidence": confidence_metrics,
        "latency": {
            "total_time_seconds": round(total_time, 3),
            "total_time_ms": round(total_time * 1000, 2),
            "breakdown": {
                "chain_initialization_ms": round(chain_init_time * 1000, 2),
                "query_execution_ms": round(query_time * 1000, 2)
            }
        },
        "metadata": {
            "model": LLM_MODEL,
            "embedding_model": EMBED_MODEL,
            "top_k": TOP_K,
            "timestamp": time.time()
        }
    }
