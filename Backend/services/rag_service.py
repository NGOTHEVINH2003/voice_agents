from Backend.rag.query import get_rag_chain

def query_rag(question: str):
    chain = get_rag_chain()
    result = chain.invoke({"query": question})
    return {
        "answer": result["result"],
        "sources": [doc.metadata.get("source", "") for doc in result["source_documents"]]
    }
