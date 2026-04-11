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

EXPANSION_PROMPT = ChatPromptTemplate.from_messages([
    (
        "system",
        "You are an expert at reformulating technical interview questions. "
        "Given a question, generate {n} alternative phrasings that capture the same intent "
        "but use different terminology or framing. This helps retrieve more relevant context.\n"
        "Return only the questions, one per line, with no numbering or extra text.",
    ),
    ("human", "{question}"),
])

ANSWER_PROMPT = ChatPromptTemplate.from_messages([
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


def _expand_query(question: str, n: int = 3) -> list[str]:
    """Generate n alternative phrasings of the question."""
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)
    chain = EXPANSION_PROMPT | llm | StrOutputParser()
    result = chain.invoke({"question": question, "n": n})
    expansions = [line.strip() for line in result.strip().splitlines() if line.strip()]
    return expansions[:n]


def ask(question: str, k: int = 4) -> tuple[str, list[SourceChunk], list[str]]:
    """
    Returns (answer, retrieved_chunks, expanded_queries).

    Uses query expansion: generates alternative phrasings, retrieves chunks
    for each, deduplicates by chunk_index keeping the highest relevance score,
    then selects the top-k for the LLM context.
    """
    vectorstore = _get_vectorstore()

    expanded_queries = _expand_query(question, n=3)
    all_queries = [question] + expanded_queries

    # Retrieve for each query, deduplicate by chunk_index (keep best score)
    best_by_index: dict[int, tuple] = {}  # chunk_index -> (doc, score)
    for query in all_queries:
        results = vectorstore.similarity_search_with_relevance_scores(query, k=k)
        for doc, score in results:
            idx = doc.metadata.get("chunk_index", id(doc))
            if idx not in best_by_index or score > best_by_index[idx][1]:
                best_by_index[idx] = (doc, score)

    # Sort by relevance score descending, take top-k
    top_results = sorted(best_by_index.values(), key=lambda x: x[1], reverse=True)[:k]

    source_chunks = [
        SourceChunk(
            content=doc.page_content,
            source=doc.metadata.get("source", "study-guide.txt"),
            chunk_index=doc.metadata.get("chunk_index", -1),
            relevance_score=round(score, 4),
        )
        for doc, score in top_results
    ]

    context = "\n\n---\n\n".join(chunk.content for chunk in source_chunks)

    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    chain = (
        {"context": RunnablePassthrough(), "question": RunnablePassthrough()}
        | ANSWER_PROMPT
        | llm
        | StrOutputParser()
    )
    answer = chain.invoke({"context": context, "question": question})

    return answer, source_chunks, expanded_queries
