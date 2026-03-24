# Streamlit UI — AI Document Assistant (продающий лендинг + демо)

import os

import streamlit as st
from dotenv import load_dotenv

from rag_pipeline import ask, ask_stream, load_and_index, load_demo_docs, load_vectorstore_if_exists

load_dotenv()

# ─── Конфигурация страницы ────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI-ассистент по документам | Демо",
    page_icon="🤖",
    layout="wide",
)

# ─── Проверка API ключа ───────────────────────────────────────────────────────
if not os.getenv("OPENAI_API_KEY"):
    st.error(
        "❌ OPENAI_API_KEY не найден.\n\n"
        "1. Скопируйте `.env.example` → `.env`\n"
        "2. Вставьте ваш ключ: `OPENAI_API_KEY=sk-...`\n"
        "3. Перезапустите: `streamlit run app.py`"
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
if "question_count" not in st.session_state:
    st.session_state["question_count"] = 0
if "pending_question" not in st.session_state:
    st.session_state["pending_question"] = None

# ─── Автозагрузка демо-документов ────────────────────────────────────────────
if not st.session_state["demo_loaded"]:
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

# ─── SIDEBAR ──────────────────────────────────────────────────────────────────
with st.sidebar:

    # Загрузка документов
    st.markdown("### 📂 Ваши документы")
    uploaded_files = st.file_uploader(
        "Загрузите PDF (до 20 МБ)",
        accept_multiple_files=True,
        type=["pdf"],
    )
    if st.button("⚡ Подключить документы", type="primary", use_container_width=True):
        if uploaded_files:
            oversized = [f.name for f in uploaded_files if f.size > 20 * 1024 * 1024]
            if oversized:
                for fname in oversized:
                    st.error(f"❌ {fname}: файл больше 20 МБ.")
            else:
                with st.spinner("Обрабатываю документы..."):
                    retriever, chunks = load_and_index(uploaded_files)
                    st.session_state["retriever"] = retriever
                    st.session_state["indexed_files"] = [f.name for f in uploaded_files]
                st.success(f"✅ Готово! Загружено {len(uploaded_files)} файлов, {chunks} фрагментов")
        else:
            st.warning("Сначала выберите PDF файлы.")

    if st.session_state["indexed_files"]:
        st.markdown("**Активные документы:**")
        for fname in st.session_state["indexed_files"]:
            st.markdown(f"✅ {fname}")

    st.divider()

    # Что вы получите
    st.markdown("### 🎁 Что вы получите")
    st.markdown(
        "✔️ Готовый AI-ассистент под ваши документы  \n"
        "✔️ Настройка под ваш бизнес и процессы  \n"
        "✔️ Интеграция в Telegram или на сайт  \n"
        "✔️ Поддержка и доработки"
    )

    st.divider()

    # Где используется
    st.markdown("### 🏢 Где используется")
    st.markdown(
        "📘 Обучение новых сотрудников  \n"
        "📋 HR и кадровые документы  \n"
        "⚙️ Технические инструкции  \n"
        "🗂️ База знаний компании"
    )

    st.divider()

    # Работает где удобно
    st.markdown("### 🔌 Работает там, где удобно")
    st.markdown(
        "🌐 В веб-интерфейсе  \n"
        "💬 В Telegram (сотрудники спрашивают прямо в чате)  \n"
        "🔗 Встраивается на сайт или в систему"
    )

    st.divider()

    # CTA
    st.markdown("#### 💼 Хотите такого же для вашей компании?")
    st.link_button(
        "🚀 Хочу такой же для бизнеса",
        "https://kwork.ru/user/yourprofile",
        use_container_width=True,
    )

    st.divider()

    if st.button("🧹 Очистить историю чата", use_container_width=True):
        st.session_state["messages"] = []
        st.session_state["question_count"] = 0
        st.rerun()

    st.caption(f"� Вопросов в демо: {st.session_state['question_count']} / 20")

# ─── ГЛАВНЫЙ ЭКРАН ────────────────────────────────────────────────────────────

# Оффер
st.markdown(
    """
    <h1 style="font-size:2.2rem; margin-bottom:0.2rem;">
        🤖 ИИ-ассистент по вашим документам
    </h1>
    <p style="font-size:1.15rem; color:#555; margin-top:0;">
        Сотрудники получают точные ответы по инструкциям и регламентам — за секунды, без ручного поиска.
    </p>
    """,
    unsafe_allow_html=True,
)

# Блок ценности
st.markdown(
    """
    <div style="background:#f0f7ff; border-radius:12px; padding:16px 20px; margin:16px 0;">
        <b>💡 Что это даёт бизнесу:</b><br><br>
        ⏱️ &nbsp;Сотрудники не тратят время на поиск по PDF и папкам<br>
        🎓 &nbsp;Новые сотрудники обучаются в 2 раза быстрее<br>
        ✅ &nbsp;Меньше ошибок при работе с инструкциями<br>
        🕐 &nbsp;Доступ к знаниям компании 24/7
    </div>
    """,
    unsafe_allow_html=True,
)

# Микро-инструкция
st.markdown(
    """
    <div style="background:#f9f9f9; border-radius:10px; padding:12px 18px; margin-bottom:16px; font-size:0.95rem;">
        <b>🚀 Как попробовать прямо сейчас:</b> &nbsp;
        <span style="color:#555;">
        1️⃣ Демо-документы уже загружены &nbsp;→&nbsp;
        2️⃣ Нажмите на пример вопроса или напишите свой &nbsp;→&nbsp;
        3️⃣ Получите ответ с указанием источника
        </span>
    </div>
    """,
    unsafe_allow_html=True,
)

# Примеры вопросов
st.markdown("**Попробуйте — нажмите на вопрос:**")
example_questions = [
    "Какие штрафы указаны в договоре?",
    "Сколько дней отпуска у сотрудников?",
    "Как связаться с HR?",
    "Сделай краткое резюме договора",
]
cols = st.columns(len(example_questions))
for col, eq in zip(cols, example_questions):
    if col.button(eq, use_container_width=True):
        st.session_state["pending_question"] = eq
        st.rerun()

st.divider()

# ─── ЧАТ ─────────────────────────────────────────────────────────────────────

# История сообщений
for msg in st.session_state["messages"]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg["role"] == "assistant" and msg.get("sources"):
            n = len(msg["sources"])
            if n >= 3:
                conf = "🟢 высокая"
            elif n >= 1:
                conf = "🟡 средняя"
            else:
                conf = "🔴 низкая"
            st.caption(f"🔍 Найдено {n} фрагментов  |  Уверенность: {conf}")
            with st.expander("📎 Источники"):
                for src in msg["sources"]:
                    meta = src.get("metadata", {})
                    fname = meta.get("source_file", meta.get("source", "unknown"))
                    page = meta.get("page", "?")
                    st.markdown(f"**{fname} | стр. {page}**")
                    st.caption(src.get("text", "")[:200])
                    st.divider()

# CTA после первого ответа
if st.session_state["messages"]:
    st.markdown(
        """
        <div style="background:#fff3cd; border-radius:10px; padding:12px 18px; margin:8px 0; font-size:0.95rem;">
            💼 <b>Хотите такого же AI-ассистента для вашей компании?</b>
            &nbsp; Настроим под ваши документы и процессы.
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.link_button("📩 Оставить заявку", "https://kwork.ru/user/yourprofile")

# Поле ввода
if st.session_state["pending_question"]:
    question = st.session_state["pending_question"]
    st.session_state["pending_question"] = None
else:
    question = st.chat_input("Задайте вопрос по документам...")

if question:
    if not st.session_state["retriever"]:
        st.error("Документы ещё загружаются. Подождите секунду и попробуйте снова.")
        st.stop()

    if st.session_state["question_count"] >= 20:
        st.warning("⚠️ Лимит демо исчерпан (20 вопросов). Нажмите «Очистить историю» для сброса.")
        st.stop()

    st.session_state["messages"].append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    # Формируем историю (пары human/ai)
    chat_history = []
    msgs = st.session_state["messages"][:-1]
    i = 0
    while i < len(msgs) - 1:
        if msgs[i]["role"] == "user" and msgs[i + 1]["role"] == "assistant":
            chat_history.append((msgs[i]["content"], msgs[i + 1]["content"]))
            i += 2
        else:
            i += 1

    with st.chat_message("assistant"):
        token_gen, source_docs = ask_stream(question, st.session_state["retriever"], chat_history)
        answer = st.write_stream(token_gen)

        n_sources = len(source_docs)
        if n_sources >= 3:
            confidence_label = "🟢 высокая"
        elif n_sources >= 1:
            confidence_label = "🟡 средняя"
        else:
            confidence_label = "🔴 низкая"
        st.caption(f"🔍 Найдено {n_sources} фрагментов  |  Уверенность: {confidence_label}")

        sources_data = []
        if source_docs:
            with st.expander("📎 Источники"):
                for doc in source_docs:
                    meta = doc.metadata
                    fname = meta.get("source_file", meta.get("source", "unknown"))
                    page = meta.get("page", "?")
                    st.markdown(f"**{fname} | стр. {page}**")
                    st.caption(doc.page_content[:200])
                    st.divider()
                    sources_data.append({"metadata": meta, "text": doc.page_content})

    st.session_state["question_count"] += 1
    st.session_state["messages"].append({
        "role": "assistant",
        "content": answer,
        "sources": sources_data,
    })
    st.rerun()
