# RAG-пайплайн: индексация PDF и ответы на вопросы

import os
import tempfile
from pathlib import Path

from dotenv import load_dotenv
from langchain_classic.chains import ConversationalRetrievalChain
from langchain_classic.memory import ConversationBufferMemory
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_community.document_loaders import PyPDFLoader
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from prompts import qa_prompt

# Загружаем переменные окружения из .env
load_dotenv()

# Директория для хранения векторной базы
CHROMA_DIR = "./chroma_db"
DEMO_DOCS_DIR = Path(__file__).parent / "demo_docs"


def _get_embeddings():
    """Возвращает модель эмбеддингов OpenAI."""
    return OpenAIEmbeddings(model="text-embedding-3-small")


def _get_llm(streaming: bool = False):
    """Возвращает языковую модель GPT-4o-mini."""
    return ChatOpenAI(model="gpt-4o-mini", temperature=0, streaming=streaming)


def load_vectorstore_if_exists():
    """
    Проверяет наличие сохранённой ChromaDB и возвращает retriever.

    Returns:
        retriever если база существует, иначе None
    """
    chroma_path = Path(CHROMA_DIR)
    # Проверяем что папка существует и не пустая
    if chroma_path.exists() and any(chroma_path.iterdir()):
        vectorstore = Chroma(
            persist_directory=CHROMA_DIR,
            embedding_function=_get_embeddings(),
        )
        return vectorstore.as_retriever(search_kwargs={"k": 4})
    return None


def _build_retriever(docs):
    """
    Разбивает документы на чанки, сохраняет в ChromaDB и возвращает retriever.
    
    Args:
        docs: список LangChain Document объектов
    
    Returns:
        retriever с k=4
    """
    # Разбиваем на чанки
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
    )
    chunks = splitter.split_documents(docs)

    # Обновляем метаданные каждого чанка
    for chunk in chunks:
        meta = chunk.metadata
        # source_file — имя файла (без полного пути)
        source = meta.get("source", "")
        meta["source_file"] = Path(source).name if source else "unknown"
        # page — номер страницы (PyPDFLoader уже добавляет "page", 0-based → делаем 1-based)
        meta["page"] = meta.get("page", 0) + 1

    # Сохраняем в ChromaDB
    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=_get_embeddings(),
        persist_directory=CHROMA_DIR,
    )

    retriever = vectorstore.as_retriever(search_kwargs={"k": 4})
    return retriever, len(chunks)


def load_and_index(uploaded_files):
    """
    Принимает список файлов из st.file_uploader, индексирует их в ChromaDB.

    Args:
        uploaded_files: список UploadedFile объектов из Streamlit

    Returns:
        tuple: (retriever, total_chunks)
    """
    all_docs = []

    for uploaded_file in uploaded_files:
        # Сохраняем загруженный файл во временный файл на диске
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(uploaded_file.read())
            tmp_path = tmp.name

        try:
            loader = PyPDFLoader(tmp_path)
            docs = loader.load()
            # Проставляем имя исходного файла в метаданные
            for doc in docs:
                doc.metadata["source"] = uploaded_file.name
            all_docs.extend(docs)
        finally:
            os.unlink(tmp_path)

    retriever, total_chunks = _build_retriever(all_docs)
    return retriever, total_chunks


def load_demo_docs():
    """
    Загружает все PDF из папки demo_docs/ и индексирует их.

    Returns:
        tuple: (retriever, total_chunks) или (None, 0) если папка пуста
    """
    pdf_files = list(DEMO_DOCS_DIR.glob("*.pdf"))
    if not pdf_files:
        return None, 0

    all_docs = []
    for pdf_path in pdf_files:
        loader = PyPDFLoader(str(pdf_path))
        docs = loader.load()
        # Проставляем имя файла в метаданные
        for doc in docs:
            doc.metadata["source"] = pdf_path.name
        all_docs.extend(docs)

    retriever, total_chunks = _build_retriever(all_docs)
    return retriever, total_chunks


def ask_stream(question, retriever, chat_history):
    """
    Задаёт вопрос и возвращает генератор для потокового вывода.
    Сначала собирает source_documents через обычный вызов, затем стримит ответ.

    Returns:
        tuple: (generator, source_documents)
    """
    # Получаем релевантные документы через retriever
    source_docs = retriever.invoke(question)

    # Формируем контекст из документов с метаданными
    context_parts = []
    for doc in source_docs:
        meta = doc.metadata
        fname = meta.get("source_file", meta.get("source", "unknown"))
        page = meta.get("page", "?")
        context_parts.append(f"[Источник: {fname}, стр. {page}]\n{doc.page_content}")
    context = "\n\n".join(context_parts)

    # Формируем историю как строку
    history_str = "\n".join(
        f"Human: {h}\nAssistant: {a}" for h, a in chat_history
    )

    # Формируем промпт
    messages = qa_prompt.format_messages(
        context=context,
        chat_history=history_str,
        question=question,
    )

    llm = _get_llm(streaming=True)

    def token_generator():
        for chunk in llm.stream(messages):
            yield chunk.content

    return token_generator(), source_docs


def ask(question, retriever, chat_history):
    """
    Задаёт вопрос через ConversationalRetrievalChain.

    Args:
        question: строка с вопросом пользователя
        retriever: retriever из ChromaDB
        chat_history: список кортежей (human, ai) или пустой список

    Returns:
        dict с ключами "answer" и "source_documents"
    """
    llm = _get_llm()

    # Память для хранения истории диалога
    memory = ConversationBufferMemory(
        memory_key="chat_history",
        return_messages=True,
        output_key="answer",
    )

    # Восстанавливаем историю в память
    for human_msg, ai_msg in chat_history:
        memory.chat_memory.add_user_message(human_msg)
        memory.chat_memory.add_ai_message(ai_msg)

    # Создаём цепочку
    chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=retriever,
        memory=memory,
        return_source_documents=True,
        combine_docs_chain_kwargs={"prompt": qa_prompt},
        output_key="answer",
    )

    result = chain.invoke({"question": question})
    return {
        "answer": result["answer"],
        "source_documents": result.get("source_documents", []),
    }
