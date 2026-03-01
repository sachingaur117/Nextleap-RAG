import os
import json
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain.docstore.document import Document

DATA_DIR = "../phase1_data_acquisition/data"
DB_DIR = "./chroma_db"

def format_course_data_to_text(data):
    """Converts the JSON course data into a coherent Markdown string for embedding."""
    title = data.get("title", "Unknown Course")
    
    content = f"# Course: {title}\n\n"
    
    if data.get("hero_details"):
        content += "## Overview\n"
        content += "\n".join(f"- {item}" for item in data["hero_details"]) + "\n\n"
        
    cost_info = data.get("cost_info", {})
    if cost_info:
        content += "## Cost and Enrollment\n"
        if "cohort_start" in cost_info:
             content += f"- **Start Date**: {cost_info['cohort_start']}\n"
        if "emi" in cost_info:
             content += f"- **EMI**: {cost_info['emi']}\n"
        if "pricing" in cost_info:
             content += f"- **Pricing**: {', '.join(cost_info['pricing'])}\n"
        if "price_increase" in cost_info:
             content += f"- **Price Alert**: {cost_info['price_increase']}\n"
        content += "\n"
             
    if data.get("placement_support"):
        content += "## Placement Support\n"
        content += "\n".join(f"- {item}" for item in data["placement_support"]) + "\n\n"
        
    if data.get("schedule"):
        content += "## Schedule\n"
        content += "\n".join(f"- {item}" for item in data["schedule"]) + "\n\n"
        
    if data.get("instructors"):
        content += "## Instructors\n"
        content += "\n".join(f"- {item}" for item in data["instructors"]) + "\n\n"

    return content

def main():
    documents = []
    
    if not os.path.exists(DATA_DIR):
        print(f"Data directory {DATA_DIR} not found. Run phase 1 first.")
        return

    # 1. Read and format data
    for filename in os.listdir(DATA_DIR):
        if filename.endswith(".json"):
            file_path = os.path.join(DATA_DIR, filename)
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                
            url = data.get("url", "unknown_url")
            title = data.get("title", filename.split(".")[0])
            
            text_content = format_course_data_to_text(data)
            
            # Create a Langchain Document
            # IMPORTANT: Source URL is saved in metadata
            meta = {
                "source": url, 
                "course": title
            }
            doc = Document(page_content=text_content, metadata=meta)
            documents.append(doc)
            
            print(f"Loaded {filename} - {url}")

    if not documents:
        print("No documents found to process.")
        return

    # 2. Split text into chunks
    # Chunking is crucial for vector retrieval so that the LLM only gets relevant parts of the text
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        separators=["\n\n", "\n", " ", ""]
    )
    
    chunked_docs = text_splitter.split_documents(documents)
    print(f"Created {len(chunked_docs)} chunks from {len(documents)} courses.")

    # 3. Create Embeddings & Store in Chroma
    # all-MiniLM-L6-v2 is a great lightweight embedding model that runs locally
    print("Loading embedding model...")
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    
    print("Generating embeddings and saving to ChromaDB...")
    vectorstore = Chroma.from_documents(
        documents=chunked_docs,
        embedding=embeddings,
        persist_directory=DB_DIR
    )
    
    print(f"Successfully constructed Knowledge Base at {DB_DIR}")

if __name__ == "__main__":
    main()
