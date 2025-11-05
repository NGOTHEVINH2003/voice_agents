from Backend.config import settings
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.tools import tool
from langchain.agents import AgentExecutor, create_tool_calling_agent
from Backend.services.calendar_service import get_calendar_tools, GoogleCalendarService

from langchain_community.embeddings import HuggingFaceBgeEmbeddings
from langchain_community.vectorstores import FAISS
import asyncio
from datetime import datetime, timedelta
from typing import List


class LangChainAgent:
    """
    MANAGE THE CONVERSATIONAL AGENT USING LANGCHAIN AND GG GEMINI.
    INCLUDE CHAT HISTORY MANAGEMENT
    """

    def __init__(self, google_api_key: str, calendar_service: GoogleCalendarService):
        print("Initializing Langchain agent(Gemini)...")
        try:
            self.llm = ChatGoogleGenerativeAI(
                google_api_key=google_api_key,
                model=settings.LLM_MODEL
            )
        except Exception as e:
            print(f"Failed to initialize ChatGoogleGenerativeAI: {e}")
            raise
    
        try:
            print("Initializing Retriever for rag...")
            embeddings = HuggingFaceBgeEmbeddings(
                model_name=settings.EMBEDDING_MODEL,
                encode_kwargs={"normalize_embeddings": True}
            )

            vectorstore = FAISS.load_local(
                settings.FAISS_INDEX_DIR,
                embeddings,
                allow_dangerous_deserialization=True
            )

            self.retriever = vectorstore.as_retriever(
                search_kwargs={"k": settings.TOP_K}
            )

            print("retriever initialized successfully.")
        except Exception as e:
            print(f"ERROR: CANNOT INITIALIZED RAG RETRIEVER: {e}")
            print("MAKE SURE FAISS_INDEX_DIR AND EMBEDDING_MODEL SETUP CORRECTLY")
            raise

        @tool
        async def perform_rag_tool(query: str) -> str:
            """Searches the internal knowledge base (RAG) for answers.
            Use this tool for any questions about company policy, internal data, or general knowledge.
            Do NOT use this tool for scheduling or calendar questions."""
            return await self._perform_rag_query(query)
        
        # @tool
        # def get_current_datetime() -> str:
        #     """Returns the current date and time in Vietnam timezone.
        #     ALWAYS use this tool first when:
        #     - User mentions relative dates like 'today', 'tomorrow', 'next week', 'next month'
        #     - Creating or searching for calendar events
        #     - Any time calculation is needed
        #     This ensures you have accurate current time for all operations."""
        #     now = datetime.now()
        #     return (f"Current date and time: {now.strftime('%Y-%m-%d %H:%M:%S')} "
        #            f"({now.strftime('%A, %B %d, %Y')})")
        
        calendar_tools = get_calendar_tools(service_instance=calendar_service)

        self.tools = [perform_rag_tool] + calendar_tools

        # Lấy thời gian hiện tại cho system prompt
        now = datetime.now()
        current_datetime = now.strftime('%Y-%m-%d %H:%M:%S')
        current_day = now.strftime('%A')
        today_date = now.strftime('%Y-%m-%d')
        tomorrow_date = (now + timedelta(days=1)).strftime('%Y-%m-%d')

        prompt = f"""You are a helpful AI assistant with calendar management capabilities.

**CRITICAL: You will be provided with the current date and time in the context for EVERY turn. You MUST use this information to resolve all relative dates.**

You have access to the following tools:
1. 'perform_rag_tool' — Search the internal knowledge base (RAG)
2. 'GoogleCalendar' tools — List, create, update, and delete calendar events

**Behavior Rules:**

1. **Date Handling (MOST IMPORTANT):**
   - ALWAYS use the 'current_datetime' provided in the system context to resolve dates.
   - When user says:
     * 'today' → use the current date
     * 'tomorrow' → add 1 day to the current date
     * 'next week' → add 7 days to the current date
     * 'next Monday' → find the next occurrence of Monday after the current date

2. **Calendar Event Creation:**
   - If user doesn't specify end time: set to 1 hour after start time
   - If user doesn't specify title: use "Meeting" as default
   - Always confirm the exact date and time before creating

3. **Communication:**
   - Always explain what actions you are taking
   - Confirm the final action with exact date and time
   - If date is ambiguous, ask for clarification

4. **Tool Selection:**
   - General questions → use 'perform_rag_tool'
   - Calendar/scheduling questions → use 'GoogleCalendar' tools

**Example workflow for "schedule meeting tomorrow at 2pm":**
1. System provides current time, e.g., "2025-11-05 16:20:00".
2. You calculate tomorrow → "2025-11-06".
3. You call create_calendar_event for 2025-11-06 14:00:00.
4. You confirm: "I've scheduled your meeting for tomorrow, November 6th at 2:00 PM"

Your goal is to be a smart, accurate scheduling assistant who never hallucinates dates."""

        self.prompt = ChatPromptTemplate.from_messages([
            ("system", prompt),
            MessagesPlaceholder(variable_name="chat_history"),
            ("system", "CONTEXT: Current Date/Time is {current_datetime}"),
            ("user", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad")
        ])
        
        agent = create_tool_calling_agent(self.llm, self.tools, self.prompt)

        agent_executor = AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=True
        )

        self.store = {}
        self.chain_with_history = RunnableWithMessageHistory(
            agent_executor,
            self.get_session_history,
            input_messages_key="input",
            history_messages_key="chat_history"
        )
        print("Langchain initialize successfully")

    def get_session_history(self, session_id: str) -> ChatMessageHistory:
        """Retrieves or creates a chat history for a given session ID."""
        if session_id not in self.store:
            print(f"Creating new chat history for session: {session_id}")
            self.store[session_id] = ChatMessageHistory()
        return self.store[session_id]
  
    async def _perform_rag_query(self, query: str) -> str:
        try:
            docs = await asyncio.to_thread(
                self.retriever.get_relevant_documents,
                query
            )
            if not docs:
                print("RAG query returned no documents.")
                return "Không tìm thấy thông tin nào liên quan đến câu hỏi của bạn."
            
            context = "\n\n---\n\n".join([doc.page_content for doc in docs])
            print(f"RAG context retrieved ({len(docs)} docs).")
            return context
        except Exception as e:
            print(f"Rag retrieval error: {e}")
            return "Information not found."
        
    async def process_text(self, text: str, session_id: str) -> str:
        """
        Xử lý văn bản đầu vào của người dùng thông qua agent executor.
        Thêm context về thời gian hiện tại vào mỗi request.
        """
        print(f"Agent processing text for session {session_id}: '{text}'")
        
        current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S %A")
        
        try:
            config = {"configurable": {"session_id": session_id}}
            
            response = await self.chain_with_history.ainvoke(
                {
                    "input": text,
                    "current_datetime": current_datetime
                },
                config=config
            )
            
            output_text = response.get('output', 'Agent does not return a response.')
            print(f"Agent response: {output_text}")
            return output_text

        except Exception as e:
            print(f"Lỗi khi xử lý văn bản trong agent: {e}")
            return "Tôi xin lỗi, tôi đã gặp lỗi. Vui lòng thử lại."