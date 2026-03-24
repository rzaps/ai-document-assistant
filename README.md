# 🤖 AI Document Assistant

AI-чатбот для работы с PDF-документами. Задавайте вопросы — получайте ответы строго по содержимому документов с указанием источника и страницы.

![Python](https://img.shields.io/badge/Python-3.11-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-1.x-red)
![LangChain](https://img.shields.io/badge/LangChain-latest-green)
![ChromaDB](https://img.shields.io/badge/ChromaDB-latest-purple)

## Демо

Загрузите свои PDF или используйте встроенные тестовые документы:
- `contract.pdf` — договор об оказании услуг
- `faq.pdf` — FAQ интернет-магазина
- `hr_policy.pdf` — кадровая политика компании

## Возможности

- Загрузка PDF-документов через веб-интерфейс
- Ответы строго по содержимому документов (без галлюцинаций)
- Указание источника и номера страницы для каждого факта
- Потоковый вывод ответа (streaming)
- Персистентная векторная база (ChromaDB)
- Индикатор уверенности ответа
- История диалога в рамках сессии
- Ограничение размера файла (макс. 20MB)
- Rate limit: 20 вопросов за сессию

## Стек технологий

| Компонент | Технология |
|-----------|-----------|
| UI | Streamlit |
| LLM | GPT-4o-mini (OpenAI) |
| Эмбеддинги | text-embedding-3-small (OpenAI) |
| Векторная база | ChromaDB |
| RAG-фреймворк | LangChain |
| Парсинг PDF | PyPDF |

## Структура проекта

```
project/
├── app.py               ← Streamlit UI
├── rag_pipeline.py      ← RAG логика (индексация, поиск, ответы)
├── prompts.py           ← Промпты для LLM
├── requirements.txt     ← Зависимости
├── .env.example         ← Пример конфига
├── create_demo_docs.py  ← Генератор тестовых PDF
└── demo_docs/
    ├── contract.pdf
    ├── faq.pdf
    └── hr_policy.pdf
```

## Установка и запуск

### 1. Клонировать репозиторий

```bash
git clone https://github.com/your-username/ai-document-assistant.git
cd ai-document-assistant/project
```

### 2. Создать виртуальное окружение

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Установить зависимости

```bash
pip install -r requirements.txt
```

### 4. Настроить API ключ

```bash
cp .env.example .env
```

Откройте `.env` и вставьте ваш ключ:

```
OPENAI_API_KEY=sk-...
```

Получить ключ можно на [platform.openai.com](https://platform.openai.com/api-keys).

### 5. Запустить приложение

```bash
streamlit run app.py
```

Приложение откроется в браузере по адресу `http://localhost:8501`.

## Как использовать

1. При запуске автоматически загружаются демо-документы
2. Введите вопрос в поле чата или нажмите одну из кнопок-примеров
3. AI ответит со ссылкой на источник и номер страницы
4. Для загрузки своих документов используйте sidebar → выберите PDF → нажмите «Загрузить и индексировать»

## Генерация тестовых документов

Если папка `demo_docs/` пустая, запустите:

```bash
python create_demo_docs.py
```

## Переменные окружения

| Переменная | Описание |
|-----------|---------|
| `OPENAI_API_KEY` | API ключ OpenAI (обязательно) |

## Лицензия

MIT
