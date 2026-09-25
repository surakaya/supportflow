# SupportFlow

SupportFlow, gelen müşteri mesajlarını aşağıdaki kriterlere göre sınıflandıran çok kiracılı (multi-tenant) bir destek talebi (ticket) akış sistemidir:
- `category` (kategori)
- `urgency` (aciliyet)
- `priority` (öncelik)
- `confidence` (güven skoru)

İçerdiği bileşenler:
- FastAPI backend
- ML akışı (DVC ile yönetilir)
- Müşteri arayüzü (widget) + admin panel modu
- MySQL veritabanı
- Hız sınırlaması (Rate limiting - Redis uyumlu)

## 1) Proje Yapısı

- `/Users/sura/Desktop/masaustu/supportflow/backend` -> API, iş mantığı, veritabanı erişimi
- `/Users/sura/Desktop/masaustu/supportflow/frontend` -> widget arayüzü (müşteri + admin modu)
- `/Users/sura/Desktop/masaustu/supportflow/ml` -> eğitim/değerlendirme/çıkarım dosyaları
- `/Users/sura/Desktop/masaustu/supportflow/db` -> şema + başlangıç (seed) SQL'i
- `/Users/sura/Desktop/masaustu/supportflow/docker` -> container yapılandırması

## 2) Temel Akış

1. Kullanıcı widget üzerinden mesaj gönderir.
2. Backend API anahtarını, hız sınırını (rate limit) ve işlem tekrarı önleme (idempotency) durumunu doğrular.
3. Makine öğrenimi (ML) `category`, `urgency` ve `confidence` değerlerini döndürür.
4. Backend `priority` değerini hesaplar.
5. Destek talebi (ticket) MySQL'e kaydedilir.
6. Admin paneli talepleri listeler ve en son tahmin detaylarını gösterir.

## 3) Yerel Çalıştırma (Docker Olmadan)

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

Açın:
- Müşteri modu: [http://127.0.0.1:5173](http://127.0.0.1:5173)
- Admin modu: [http://127.0.0.1:5173/?mode=admin](http://127.0.0.1:5173/?mode=admin)

## 4) Docker ile Çalıştırma

```bash
cd /Users/sura/Desktop/masaustu/supportflow/docker
docker compose up -d --build
docker compose ps
```

Açın:
- Frontend: [http://127.0.0.1:5173](http://127.0.0.1:5173)
- Backend sağlık durumu (health): [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

Notlar:
- Yerel `3306` portuyla çakışmayı önlemek için compose dosyasında veritabanı (DB) host portu `3307` olarak ayarlanmıştır.
- Dağıtık hız sınırlaması (rate limit) altyapısına hazırlık amacıyla bir Redis container'ı dahil edilmiştir.

## 5) Hızlı API Kontrolleri

### Analiz

```bash
curl -X POST "http://127.0.0.1:8000/analyze/" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: test_api_key_123" \
  -H "Idempotency-Key: demo-1" \
  -d '{"message":"sifrem kontrolum disinda degistirilmis"}'
```

### Talepler (Tickets)

```bash
curl -X GET "http://127.0.0.1:8000/tickets/" \
  -H "X-API-Key: test_api_key_123"
```

## 6) Makine Öğrenimi (ML) Akışı (DVC)

Modelleri ve metrikleri yeniden oluşturun:

```bash
cd /Users/sura/Desktop/masaustu/supportflow
dvc repro --force
dvc metrics show
```

İzlenen çıktılar:
- `/Users/sura/Desktop/masaustu/supportflow/ml/models/category_model.pkl`
- `/Users/sura/Desktop/masaustu/supportflow/ml/models/urgency_model.pkl`
- `/Users/sura/Desktop/masaustu/supportflow/ml/models/model_metadata.json`
- `/Users/sura/Desktop/masaustu/supportflow/ml/models/metrics.json`
- `/Users/sura/Desktop/masaustu/supportflow/ml/models/eval_report.txt`

## 7) Çevresel Değişkenler (Backend)

`/Users/sura/Desktop/masaustu/supportflow/backend/.env` dosyasını kullanın:

```env
DB_HOST=localhost
DB_PORT=3306
DB_NAME=supportflow
DB_USER=supportflow
DB_PASSWORD=

# İsteğe bağlı dağıtık hız sınırlandırması
# REDIS_URL=redis://localhost:6379/0
RATE_LIMIT_PER_MINUTE=20
RATE_LIMIT_WINDOW_SECONDS=60

# Örnek:
# CORS_ALLOW_ORIGINS=http://127.0.0.1:5173,http://localhost:5173
```

## 8) Güncel Canlı Ortam (Production) Notları

- Çok kiracılı (multi-tenant) erişim zorunluluğu `X-API-Key` üzerinden sağlanır.
- İşlem tekrarı önleme (idempotency) mekanizması `(company_id, idempotency_key)` kapsamına göre çalışır.
- Hız sınırlandırması (rate limit) Redis'i destekler; eğer Redis kullanılamıyorsa bellek içi (in-memory) çalışma sistemine döner (fallback).
- Düşük güven skoruna (low-confidence) sahip ML çıktıları için backend, bariz yanlış sınıflandırmaları azaltmak adına deterministik destek (fallback) kuralları uygular.
