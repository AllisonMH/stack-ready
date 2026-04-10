from pathlib import Path

from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

from models import SourceChunk

load_dotenv()

CHROMA_DIR = Path(__file__).parent / "chroma_db"

PROMPT = ChatPromptTemplate.from_messages([
    (
        "system",
        "You are an expert technical interview coach. Answer the candidate's question "
        "clearly and concisely using only the provided context. If the context does not "
        "contain enough information, say so rather than guessing.\n\n"
        "Context:\n{context}",
    ),
    ("human", "{question}"),
])


def _get_vectorstore() -> Chroma:
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    return Chroma(
        persist_directory=str(CHROMA_DIR),
        embedding_function=embeddings,
        collection_name="study_guide",
    )


def ask(question: str, k: int = 4) -> tuple[str, list[SourceChunk]]:
    """
    Returns (answer, retrieved_chunks).
    Chunks include relevance scores for inspection.
    """
    vectorstore = _get_vectorstore()
    retriever_with_scores = vectorstore.similarity_search_with_relevance_scores(
        question, k=k
    )

    source_chunks = [
        SourceChunk(
            content=doc.page_content,
            source=doc.metadata.get("source", "study-guide.txt"),
            chunk_index=doc.metadata.get("chunk_index", -1),
            relevance_score=round(score, 4),
        )
        for doc, score in retriever_with_scores
    ]

    context = "\n\n---\n\n".join(chunk.content for chunk in source_chunks)

    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    chain = (
        {"context": RunnablePassthrough(), "question": RunnablePassthrough()}
        | PROMPT
        | llm
        | StrOutputParser()
    )
    answer = chain.invoke({"context": context, "question": question})

    return answer, source_chunks
