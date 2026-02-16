"""
🔥 Exemple Minimal & Clean - Memory LCEL
=========================================

Version ultra-simplifiée pour comprendre rapidement le concept.
"""

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_groq import ChatGroq
from langchain_core.output_parsers import StrOutputParser
import os
from dotenv import load_dotenv

load_dotenv()

# 1️⃣ Model
model = ChatGroq(model="openai/gpt-oss-20b", temperature=0)

# 2️⃣ Prompt avec placeholder memory
prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a senior data scientist with 10+ years of experience. 
You're mentoring junior data scientists and helping them grow their skills.

Your role is to:
- Provide clear, practical guidance on data science concepts and best practices
- Explain complex topics in an accessible way without oversimplifying
- Share real-world experience and common pitfalls to avoid
- Help debug code, review approaches, and suggest improvements
- Encourage learning while being honest about challenges

When helping junior data scientists, you should:
- Break down complex problems into manageable steps
- Explain the "why" behind recommendations, not just the "what"
- Provide code examples when relevant
- Suggest learning resources for deeper understanding
- Be patient and supportive, remembering that everyone starts somewhere

The tone should be: professional, encouraging, clear, practical, and constructive

You remember previous conversations with each junior data scientist to provide 
contextual and personalized guidance based on their experience level and past questions."""),
    MessagesPlaceholder(variable_name="history"),  # ⚠️ CRUCIAL
    ("human", "{input}")
])

# 3️⃣ LCEL pipeline
chain = prompt | model | StrOutputParser()

# 4️⃣ Stockage mémoire (par session)
store = {}

def get_session_history(session_id: str):
    if session_id not in store:
        store[session_id] = InMemoryChatMessageHistory()
    return store[session_id]

# 5️⃣ Wrap avec memory
chain_with_memory = RunnableWithMessageHistory(
    chain,
    get_session_history,
    input_messages_key="input",
    history_messages_key="history"
)

# 6️⃣ Test conversation
if __name__ == "__main__":
    session_id = "junior_ds_1"  # Session identifier for memory
    
    print("🔥 Senior Data Scientist Assistant - Conversation Mode")
    print("=" * 60)
    print("💡 Ask your data science questions!")
    print("💡 Type 'quit' or 'exit' to quit\n")
    
    while True:
        user_input = input("👤 Junior DS: ")
        
        if user_input.lower() in ['quit', 'exit', 'q']:
            print("\n👋 See you later! Keep learning!")
            break
        
        if not user_input.strip():
            continue
        
        try:
            response = chain_with_memory.invoke(
                {"input": user_input},
                config={"configurable": {"session_id": session_id}}
            )
            print(f"🤖 Senior DS: {response}\n")
        except Exception as e:
            print(f"❌ Error: {e}\n")
