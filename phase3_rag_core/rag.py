import os
from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate

# Vector DB directory path, resolved relative to this file
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Explicitly load .env from the project root so it works regardless of where the script is run from
env_path = os.path.join(BASE_DIR, "..", ".env")
load_dotenv(dotenv_path=env_path)

DB_DIR = os.path.join(BASE_DIR, "../phase2_vector_database/chroma_db")

def get_rag_chain():
    # 1. Load the existing Vector Database
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    vectorstore = Chroma(persist_directory=DB_DIR, embedding_function=embeddings)
    
    # We retrieve the top 3 most relevant chunks
    retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

    # 2. Initialize Gemini LLM
    if "GEMINI_API_KEY" not in os.environ and "GOOGLE_API_KEY" not in os.environ:
        raise ValueError("GEMINI_API_KEY or GOOGLE_API_KEY environment variable is required.")
        
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=api_key,
        temperature=0.2, # Keep temperature low for factual RAG responses
        max_tokens=None,
        timeout=None,
        max_retries=2,
    )

    # 3. Create the Guardrailed Prompt Template
    system_prompt = (
        "You are an AI assistant for Nextleap answering questions about courses, cohorts, and curricula. "
        "Use the following pieces of retrieved context to answer the user's question.\n\n"
        "STRICT GUARDRAILS:\n"
        "1. You MUST ONLY use the information provided in the context below to answer the question. Do not use outside knowledge.\n"
        "2. If the context does not contain the information to answer the question, explicitly state: 'I'm sorry, I don't have information on that available in my current database.'\n"
        "3. You MUST REFUSE to answer any queries regarding personal information, sensitive data, or questions unrelated to Nextleap courses. State that such topics are out of scope.\n"
        "4. Your answer must be concise and helpful.\n\n"
        "Context:\n{context}"
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "{input}"),
    ])

    # 4. Construct the complete RAG Pipeline
    question_answer_chain = create_stuff_documents_chain(llm, prompt)
    rag_chain = create_retrieval_chain(retriever, question_answer_chain)
    
    return rag_chain

def answer_query(query: str):
    """
    Function to be consumed by the Backend (Phase 4).
    Returns a dictionary with the final answer and the source URL(s).
    """
    try:
        chain = get_rag_chain()
        response = chain.invoke({"input": query})
        
        # Extract unique source URLs from the metadata of retrieved chunks
        sources = set()
        for doc in response.get("context", []):
            if "source" in doc.metadata:
                sources.add(doc.metadata["source"])
                
        return {
            "answer": response["answer"],
            "sources": list(sources)
        }
    except Exception as e:
        return {
            "error": str(e)
        }

if __name__ == "__main__":
    print("Initializing Nextleap RAG Core...")
    print("Type your questions below (or 'quit' to exit).")
    
    chain = get_rag_chain()
    
    while True:
        user_query = input("\nYou: ")
        if user_query.lower() in ['quit', 'exit', 'q']:
            break
            
        print("\nRetrieving...")
        result = answer_query(user_query)
        
        if "error" in result:
            print(f"Error: {result['error']}")
        else:
            print(f"\nChatbot: {result['answer']}")
            print("\nSources:")
            for source in result['sources']:
                print(f"- {source}")
