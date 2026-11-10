# Knowledge Assistant API

A Django REST Framework starter for a retrieval augmented generation (RAG) knowledge assistant. It accepts text, Markdown, and text-based PDF documents; creates embedding-backed chunks; and answers questions with source references.

## Local setup

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Set `OPENAI_API_KEY` in `.env`, then initialize and run:

```powershell
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

## API

All API endpoints require authentication. Use the Django admin to create a user, or the DRF browsable API's Basic Auth prompt for local development.

- `GET /api/health/` — health check
- `GET|POST /api/documents/` — list your documents or upload one (`title`, `file` multipart fields)
- `GET|DELETE /api/documents/{id}/` — inspect or delete one of your documents
- `POST /api/documents/{id}/reindex/` — reprocess its stored file
- `POST /api/ask/` — ask a question; JSON body: `{"question":"...", "document_ids":[1], "top_k":5}`. `document_ids` is optional.
- `GET /api/docs/` — Swagger UI

The upload request currently indexes synchronously, so keep uploads modest. Embeddings are stored in JSON and compared in application memory; this keeps local setup simple but is intended for a prototype. For larger corpora, move ingestion to Celery and store/query vectors in PostgreSQL with pgvector. Configure a strong secret, HTTPS, production database, and a dedicated auth flow before deployment.
