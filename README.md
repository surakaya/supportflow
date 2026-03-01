# SupportFlow

SupportFlow is a multi-tenant support ticket pipeline that classifies incoming customer messages by:
- `category`
- `urgency`
- `priority`
- `confidence`

It includes:
- FastAPI backend
- ML pipeline (DVC-managed)
- Customer widget + admin panel mode
- MySQL persistence
- Rate limiting (Redis-ready)

## 1) Project Structure

- `/Users/sura/Desktop/masaustu/supportflow/backend` -> API, business logic, DB access
- `/Users/sura/Desktop/masaustu/supportflow/frontend` -> widget UI (customer + admin mode)
- `/Users/sura/Desktop/masaustu/supportflow/ml` -> training/evaluation/inference assets
- `/Users/sura/Desktop/masaustu/supportflow/db` -> schema + seed SQL
- `/Users/sura/Desktop/masaustu/supportflow/docker` -> container setup

## 2) Core Flow

1. User sends message from widget.
2. Backend validates API key + rate limit + idempotency.
3. ML returns `category`, `urgency`, `confidence`.
4. Backend computes `priority`.
5. Ticket is stored in MySQL.
6. Admin panel lists tickets and shows latest prediction details.

## 3) Local Run (without Docker)

### Backend

```bash
cd /Users/sura/Desktop/masaustu/supportflow/backend
pip install -r requirements.txt
PYTHONPATH=. uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend

```bash
cd /Users/sura/Desktop/masaustu/supportflow/frontend
npm install
npm run dev -- --host
```

Open:
- Customer mode: [http://127.0.0.1:5173](http://127.0.0.1:5173)
- Admin mode: [http://127.0.0.1:5173/?mode=admin](http://127.0.0.1:5173/?mode=admin)

## 4) Docker Run

```bash
cd /Users/sura/Desktop/masaustu/supportflow/docker
docker compose up -d --build
docker compose ps
```

Open:
- Frontend: [http://127.0.0.1:5173](http://127.0.0.1:5173)
- Backend health: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

Notes:
- DB host port is `3307` in compose to avoid local `3306` conflicts.
- Redis container is included for distributed rate limit readiness.

## 5) API Quick Checks

### Analyze

```bash
curl -X POST "http://127.0.0.1:8000/analyze/" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: test_api_key_123" \
  -H "Idempotency-Key: demo-1" \
  -d '{"message":"sifrem kontrolum disinda degistirilmis"}'
```

### Tickets

```bash
curl -X GET "http://127.0.0.1:8000/tickets/" \
  -H "X-API-Key: test_api_key_123"
```

## 6) ML Pipeline (DVC)

Reproduce models + metrics:

```bash
cd /Users/sura/Desktop/masaustu/supportflow
dvc repro --force
dvc metrics show
```

Tracked outputs:
- `/Users/sura/Desktop/masaustu/supportflow/ml/models/category_model.pkl`
- `/Users/sura/Desktop/masaustu/supportflow/ml/models/urgency_model.pkl`
- `/Users/sura/Desktop/masaustu/supportflow/ml/models/model_metadata.json`
- `/Users/sura/Desktop/masaustu/supportflow/ml/models/metrics.json`
- `/Users/sura/Desktop/masaustu/supportflow/ml/models/eval_report.txt`

## 7) Environment Variables (Backend)

Use `/Users/sura/Desktop/masaustu/supportflow/backend/.env`:

```env
DB_HOST=localhost
DB_PORT=3306
DB_NAME=supportflow
DB_USER=supportflow
DB_PASSWORD=

# Optional distributed rate limit
# REDIS_URL=redis://localhost:6379/0
RATE_LIMIT_PER_MINUTE=20
RATE_LIMIT_WINDOW_SECONDS=60

# Example:
# CORS_ALLOW_ORIGINS=http://127.0.0.1:5173,http://localhost:5173
```

## 8) Current Production Notes

- Multi-tenant access is enforced via `X-API-Key`.
- Idempotency is scoped by `(company_id, idempotency_key)`.
- Rate limit supports Redis and falls back to in-memory if Redis is unavailable.
- For low-confidence ML outputs, backend applies deterministic fallback rules to reduce clearly wrong classifications.

