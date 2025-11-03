from Backend.config import settings
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory

from langchain_community.embeddings import HuggingFaceBgeEmbeddings
from langchain_community.vectorstores import FAISS
import asyncio

class LangChainAgent:
    """
    MANAGE THE CONVERSATIONAL AGENT USING LANGCHAIN AND GG GEMINI.
    INCLUDE CHAT HISTORY MANAGEMENT
    """

    def __init__(self, google_api_key: str):
        print("Initializing Langchain agent(Gemini)...")
        try:
            self.llm = ChatGoogleGenerativeAI(
                google_api_key= google_api_key,
                model= settings.LLM_MODEL
            )
        except Exception as e:
            print(f"Failed to initialize ChatGoogleGenerativeAI: {e}")
            raise
    
        try:
            print("Initializing Retriever for rag...")
            embeddings = HuggingFaceBgeEmbeddings(
                model_name = settings.EMBEDDING_MODEL,
                encode_kwargs = {"normalize_embeddings": True}
            )

            vectorstore = FAISS.load_local(
                settings.FAISS_INDEX_DIR,
                embeddings,
                allow_dangerous_deserialization=True
            )

            self.retriever = vectorstore.as_retriever(
                search_kwargs ={"k": settings.TOP_K}
            )

            print("retriever initialized successfully.")
        except Exception as e:
            print(f"ERROR: CANNOT INITIALIZED RAG RETRIEVER: {e}")
            print("MAKE SURE FAISS_INDEX_DIR AND EMBEDDING_MODEL SETUP CORRECTLY")
            raise
        
        prompt = """
        You are an AI assistant. Use the following retrieved context to answer the user's question.
        If the context doesn't contain the answer, just say you don't know.
        \n\nCONTEXT:\n{context}"""

        self.prompt = ChatPromptTemplate.from_messages([
            ("system", prompt),
            MessagesPlaceholder(variable_name="chat_history"),
            ("user", "{input}")
        ])

        chain = self.prompt |  self.llm
        self.store = {}
        self.chain_with_history = RunnableWithMessageHistory(
            chain,
            self.get_session_history,
            input_messages_key="input",
            history_messages_key="chat_history",
            input_messages_key_context_keys=["context"]
        )
        print("Langchain initialize successfully")

    def get_session_history(self, session_id: str) -> ChatMessageHistory:
        """Retrieves or creates a chat history for a given session ID."""
        if session_id not in self.store:
            print(f"Creating new chat history for session: {session_id}")
            self.store[session_id] = ChatMessageHistory()
        return self.store[session_id]
    
    async def perform_rag(self, query:str) -> str:
        try:
            docs = await asyncio.to_thread(
                self.retriever.get_relevant_documents,
                query
            )
            context = "\n\n---\n\n".join([doc.page_content for doc in docs])

            print(f"RAG context retrieved ({len(docs)} docs).")
            return context
        except Exception as e:
            print(f"Rag retrieval error: {e}")
            return "Information not found."
        
    async def process_text(self, text: str, session_id: str) -> str:
        """
        Processes user text and returns the agent's response.
        Manages history using the session_id.
        """
        print(f"Agent processing text for session {session_id}: '{text}'")
        
        try:
            context = await self.perform_rag(text)
        except Exception as e:
            print(f"RAG error: {e}")
            return "Tôi xin lỗi, tôi gặp sự cố khi truy xuất thông tin. Bạn vui lòng thử lại."

        config_for_invoke = {"configurable": {"session_id": session_id}}
        inputs = {
            "input": text,
            "context": context
        }

        try:
            response = await self.chain_with_history.ainvoke(inputs, config=config_for_invoke)
                        
            agent_response = response.content
            print(f"Agent response: '{agent_response}'")
            return agent_response
        except Exception as e:
            print(f"LangChain invocation error: {e}")
            return "Tôi xin lỗi, tôi gặp phải một lỗi. Bạn có thể lặp lại điều đó được không?"
