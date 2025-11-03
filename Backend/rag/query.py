from langchain.chains.retrieval_qa.base import RetrievalQA
from langchain_community.embeddings import HuggingFaceBgeEmbeddings
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.vectorstores import FAISS
from langchain.prompts import PromptTemplate
from Backend.config import settings

index_path = settings.FAISS_INDEX_DIR
EMBED_MODEL = settings.EMBEDDING_MODEL
GOOGLE_API_TOKEN = settings.GOOGLE_API_KEY
TOP_K = settings.TOP_K
LLM_MODEL = settings.LLM_MODEL


def get_rag_chain():
    embeddings = HuggingFaceBgeEmbeddings(
        model_name= EMBED_MODEL,
        encode_kwargs={"normalize_embeddings": True}
    )
    vectorstore = FAISS.load_local(index_path,embeddings,allow_dangerous_deserialization=True)

    retriever = vectorstore.as_retriever(search_kwargs={"k": TOP_K})

    llm = ChatGoogleGenerativeAI(
        model= LLM_MODEL,
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
        chain_type = "stuff"

    )

    return chain