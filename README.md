# SupportFlow

SupportFlow, gelen müşteri mesajlarını aşağıdaki kriterlere göre sınıflandıran çok kiracılı (multi-tenant) bir destek talebi pipeline'ıdır:

- `category` (kategori)
- `urgency` (aciliyet)
- `priority` (öncelik)
- `confidence` (güven skoru)

Proje şunları içerir:

- FastAPI backend
- DVC ile yönetilen ML pipeline
- Müşteri widget'ı + admin panel modu
- MySQL veri kalıcılığı
- Rate limiting (Redis desteğine hazır)

## 1) Proje Yapısı

- `/Users/sura/Desktop/masaustu/supportflow/backend` -> API, iş mantığı ve veritabanı erişimi
- `/Users/sura/Desktop/masaustu/supportflow/frontend` -> widget arayüzü (müşteri + admin modu)
- `/Users/sura/Desktop/masaustu/supportflow/ml` -> model eğitimi, değerlendirme ve inference dosyaları
- `/Users/sura/Desktop/masaustu/supportflow/db` -> şema + başlangıç (seed) SQL dosyaları
- `/Users/sura/Desktop/masaustu/supportflow/docker` -> container yapılandırması

## 2) Temel Akış

1. Kullanıcı widget üzerinden mesaj gönderir.
2. Backend API key, rate limit ve idempotency kontrollerini gerçekleştirir.
3. ML pipeline `category`, `urgency` ve `confidence` değerlerini üretir.
4. Backend `priority` değerini hesaplar.
5. Destek talebi MySQL veritabanına kaydedilir.
6. Admin paneli destek taleplerini listeler ve en güncel tahmin sonuçlarını gösterir.

## 3) Local Çalıştırma (Docker olmadan)

### Backend

```bash
cd /Users/sura/Desktop/masaustu/supportflow/backend
pip install -r requirements.txt
PYTHONPATH=. uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
