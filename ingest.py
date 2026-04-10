"""
Run this script once (or whenever study-guide.txt changes) to populate
the ChromaDB vector store.

    python ingest.py
"""

from pathlib import Path

from dotenv import load_dotenv
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma

load_dotenv()

STUDY_GUIDE = Path(__file__).parent / "study-guide.txt"
CHROMA_DIR = Path(__file__).parent / "chroma_db"

# ~500 tokens per chunk, 100-token overlap keeps context across boundaries
CHUNK_SIZE = 500
CHUNK_OVERLAP = 100


def ingest() -> int:
    loader = TextLoader(str(STUDY_GUIDE), encoding="utf-8")
    docs = loader.load()

    splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        model_name="text-embedding-3-small",
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
    )
    chunks = splitter.split_documents(docs)

    # Tag each chunk with its index so we can surface it in the API response
    for i, chunk in enumerate(chunks):
        chunk.metadata["chunk_index"] = i

    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

    Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=str(CHROMA_DIR),
        collection_name="study_guide",
    )

    print(f"Ingested {len(chunks)} chunks into {CHROMA_DIR}")
    return len(chunks)


if __name__ == "__main__":
    ingest()
