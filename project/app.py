# Streamlit UI для AI Document Assistant

import os

import streamlit as st
from dotenv import load_dotenv

from rag_pipeline import ask, ask_stream, load_and_index, load_demo_docs, load_vectorstore_if_exists

# Загружаем переменные окружения
load_dotenv()

# ─── Конфигурация страницы ────────────────────────────────────────────────────
st.set_page_config(page_title="AI Document Assistant", layout="wide")

# ─── Проверка API ключа ───────────────────────────────────────────────────────
if not os.getenv("OPENAI_API_KEY"):
    st.error(
        "❌ OPENAI_API_KEY не найден.\n\n"
        "1. Скопируйте файл `.env.example` → `.env`\n"
        "2. Вставьте ваш ключ: `OPENAI_API_KEY=sk-...`\n"
        "3. Перезапустите приложение: `streamlit run app.py`"
    )
    st.stop()

# ─── Инициализация состояния сессии ──────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state["messages"] = []

if "retriever" not in st.session_state:
    st.session_state["retriever"] = None

if "indexed_files" not in st.session_state:
    st.session_state["indexed_files"] = []

if "demo_loaded" not in st.session_state:
    st.session_state["demo_loaded"] = False

# Счётчик вопросов для rate limit
if "question_count" not in st.session_state:
    st.session_state["question_count"] = 0

# Вопрос от кнопки-примера
if "pending_question" not in st.session_state:
    st.session_state["pending_question"] = None

# ─── Автозагрузка демо-документов при первом запуске ─────────────────────────
if not st.session_state["demo_loaded"]:
    # Сначала пробуем загрузить существующую базу
    existing_retriever = load_vectorstore_if_exists()
    if existing_retriever:
        st.session_state["retriever"] = existing_retriever
        st.session_state["indexed_files"] = ["contract.pdf", "faq.pdf", "hr_policy.pdf"]
    else:
        with st.spinner("Загружаю демо-документы..."):
            retriever, chunks = load_demo_docs()
            if retriever:
                st.session_state["retriever"] = retriever
                st.session_state["indexed_files"] = ["contract.pdf", "faq.pdf", "hr_policy.pdf"]
    st.session_state["demo_loaded"] = True

# ─── Заголовок ────────────────────────────────────────────────────────────────
st.title("🤖 AI Document Assistant")
st.markdown('<p style="color: gray;">Задайте вопрос по вашим документам</p>', unsafe_allow_html=True)

# ─── Примеры вопросов ─────────────────────────────────────────────────────────
st.markdown("**Попробуйте задать вопрос:**")
example_questions = [
    "Какие штрафы указаны в договоре?",
    "Сколько дней отпуска у сотрудников?",
    "Как связаться с HR?",
]
cols = st.columns(len(example_questions))
for col, eq in zip(cols, example_questions):
    if col.button(eq, use_container_width=True):
        st.session_state["pending_question"] = eq
        st.rerun()

# ─── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("📂 Документы")

    # Загрузчик файлов
    uploaded_files = st.file_uploader(
        "Выберите PDF файлы",
        accept_multiple_files=True,
        type=["pdf"],
    )

    # Кнопка индексации
    if st.button("Загрузить и индексировать", type="primary"):
        if uploaded_files:
            # Проверка размера файлов (максимум 20MB)
            oversized = [f.name for f in uploaded_files if f.size > 20 * 1024 * 1024]
            if oversized:
                for fname in oversized:
                    st.error(f"❌ {fname}: Файл слишком большой. Максимум 20MB.")
            else:
                with st.spinner("Индексирую документы..."):
                    retriever, chunks = load_and_index(uploaded_files)
                    st.session_state["retriever"] = retriever
                    st.session_state["indexed_files"] = [f.name for f in uploaded_files]
                st.success(f"✅ Загружено {len(uploaded_files)} документов, {chunks} чанков")
        else:
            st.warning("Сначала выберите PDF файлы.")

    # Список загруженных файлов
    if st.session_state["indexed_files"]:
        st.markdown("**Проиндексированные файлы:**")
        for fname in st.session_state["indexed_files"]:
            st.markdown(f"✅ {fname}")

    st.divider()

    # Кнопка очистки истории
    if st.button("🧹 Очистить историю"):
        st.session_state["messages"] = []
        st.session_state["question_count"] = 0
        st.rerun()

    # Счётчик вопросов
    remaining = max(0, 20 - st.session_state["question_count"])
    st.caption(f"💬 Вопросов использовано: {st.session_state['question_count']} / 20")

    # Подсказка про демо
    st.markdown(
        '<p style="color: gray; font-size: 0.85em;">'
        "💡 Демо: в системе уже есть тестовые документы.<br>"
        "Задайте вопрос или загрузите свои PDF."
        "</p>",
        unsafe_allow_html=True,
    )

    st.divider()

    # Примеры использования
    st.markdown("**💼 Примеры использования:**")
    st.markdown(
        "• Анализ договоров  \n"
        "• Поиск по базе знаний компании  \n"
        "• Помощник для HR документов  \n"
        "• Поиск по инструкциям и регламентам"
    )

    st.divider()

    # Кнопка заказа
    st.markdown("**Нужен такой AI-ассистент для вашей компании?**")
    st.link_button("🚀 Заказать разработку", "https://kwork.ru/user/yourprofile", use_container_width=True)

# ─── Основная область — чат ───────────────────────────────────────────────────

# Рендерим историю сообщений
for msg in st.session_state["messages"]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        # Показываем источники для сообщений ассистента
        if msg["role"] == "assistant" and msg.get("sources"):
            with st.expander("📎 Источники"):
                for src in msg["sources"]:
                    meta = src.get("metadata", {})
                    fname = meta.get("source_file", meta.get("source", "unknown"))
                    page = meta.get("page", "?")
                    text_preview = src.get("text", "")[:200]
                    st.markdown(f"**{fname} | стр. {page}**")
                    st.caption(text_preview)
                    st.divider()

# Поле ввода вопроса
# Если нажата кнопка-пример — берём вопрос из pending_question, иначе из chat_input
if st.session_state["pending_question"]:
    question = st.session_state["pending_question"]
    st.session_state["pending_question"] = None
else:
    question = st.chat_input("Задайте вопрос...")
if question:
    # Проверяем наличие retriever
    if not st.session_state["retriever"]:
        st.error("Нет проиндексированных документов. Загрузите PDF или дождитесь загрузки демо.")
        st.stop()

    # Rate limit — максимум 20 вопросов за сессию
    if st.session_state["question_count"] >= 20:
        st.warning("⚠️ Лимит вопросов для демо достигнут. Нажмите «🧹 Очистить историю» для сброса.")
        st.stop()

    # Добавляем вопрос пользователя в историю
    st.session_state["messages"].append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    # Формируем историю для передачи в цепочку (пары human/ai)
    chat_history = []
    msgs = st.session_state["messages"][:-1]  # без последнего вопроса
    i = 0
    while i < len(msgs) - 1:
        if msgs[i]["role"] == "user" and msgs[i + 1]["role"] == "assistant":
            chat_history.append((msgs[i]["content"], msgs[i + 1]["content"]))
            i += 2
        else:
            i += 1

    # Получаем ответ от AI со стримингом
    with st.chat_message("assistant"):
        token_gen, source_docs = ask_stream(question, st.session_state["retriever"], chat_history)
        # Потоковый вывод ответа
        answer = st.write_stream(token_gen)

        # Индикатор уверенности ответа
        n_sources = len(source_docs)
        if n_sources >= 3:
            confidence_label = "🟢 высокая"
        elif n_sources >= 1:
            confidence_label = "🟡 средняя"
        else:
            confidence_label = "🔴 низкая"
        st.caption(f"🔍 Результаты поиска: найдено {n_sources} фрагментов документов  |  Уверенность ответа: {confidence_label}")

        # Сериализуем источники для хранения в session_state
        sources_data = []
        if source_docs:
            with st.expander("📎 Источники"):
                for doc in source_docs:
                    meta = doc.metadata
                    fname = meta.get("source_file", meta.get("source", "unknown"))
                    page = meta.get("page", "?")
                    text_preview = doc.page_content[:200]
                    st.markdown(f"**{fname} | стр. {page}**")
                    st.caption(text_preview)
                    st.divider()
                    sources_data.append({
                        "metadata": meta,
                        "text": doc.page_content,
                    })

    # Увеличиваем счётчик вопросов
    st.session_state["question_count"] += 1

    # Сохраняем ответ ассистента в историю
    st.session_state["messages"].append({
        "role": "assistant",
        "content": answer,
        "sources": sources_data,
    })
