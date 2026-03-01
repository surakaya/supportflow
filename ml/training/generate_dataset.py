import csv
import random
from pathlib import Path

random.seed(42)

OUT_PATH = Path("ml/training/tickets.csv")
SAMPLES_PER_CATEGORY = 900

CATEGORY_TEMPLATES = {
    "billing": [
        "Odeme islemi basarisiz oldu, plan {plan} icin islem tamamlanmadi.",
        "{invoice_month} faturasi iki kez kesildi.",
        "Iade talebim hala hesaba yansimadi.",
        "Fatura tutari yanlis gorunuyor.",
        "Karttan para cekildi ama paket aktif olmadi.",
        "Paket yukseltme sirasinda odeme hatasi aliyorum.",
        "Abonelik yenilemede odeme alinmadi.",
        "Faturadaki kalemlerde tutarsizlik var.",
    ],
    "technical": [
        "Sistem cok yavas, panel acilmiyor.",
        "Uygulama surekli cokuyor.",
        "Giris ekraninda 500 hatasi aliyorum.",
        "API yanit vermiyor, istekler zaman asimina dusuyor.",
        "Webhook olaylari islenmiyor.",
        "Mobil uygulama acildiktan sonra donuyor.",
        "Rapor ekrani hic yuklenmiyor.",
        "Butona basinca sistem tepki vermiyor.",
    ],
    "account": [
        "Parolam benim kontrolum disinda degistirilmis.",
        "Hesabima giris yapamiyorum.",
        "Sifre sifirlama maili gelmiyor.",
        "Hesabim kilitlendi, acil yardim gerekli.",
        "Iki asamali dogrulama kodu kabul edilmiyor.",
        "Hesap eposta adresimi degistiremiyorum.",
        "Kullanici profilime erisemiyorum.",
        "Oturum acma denemeleri basarisiz oluyor.",
    ],
}

FILLERS = {
    "plan": ["baslangic", "buyume", "isletme"],
    "invoice_month": ["Ocak", "Subat", "Mart", "Nisan", "Mayis", "Haziran"],
}

URGENCY_LEVELS = ["low", "medium", "high"]
URGENCY_WEIGHTS = {
    "billing": [0.25, 0.5, 0.25],
    "technical": [0.15, 0.35, 0.5],
    "account": [0.35, 0.45, 0.2],
}

URGENCY_CUES = {
    "low": [
        "Acil degil, uygun zamanda bakabilirsiniz.",
        "Dusuk oncelikli bir talep.",
        "Su an is akisini etkilemiyor.",
    ],
    "medium": [
        "Bugun cozulurse iyi olur.",
        "Ekipte isi etkiliyor, yakinda cozulmeli.",
        "Orta oncelikli bir sorun.",
    ],
    "high": [
        "Acil durum, sistem tamamen durdu.",
        "Kritik olay, hemen mudahale gerekli.",
        "Tum ekip calisamiyor, acil cozum gerekli.",
    ],
}


def fill_template(template: str) -> str:
    values = {key: random.choice(options) for key, options in FILLERS.items()}
    return template.format(**values)


def add_urgency_signal(message: str, urgency: str) -> str:
    cue = random.choice(URGENCY_CUES[urgency])
    if random.random() < 0.9:
        return f"{message} {cue}"
    return message


def build_rows() -> list[tuple[str, str, str]]:
    rows: list[tuple[str, str, str]] = []
    for category, templates in CATEGORY_TEMPLATES.items():
        for _ in range(SAMPLES_PER_CATEGORY):
            template = random.choice(templates)
            message = fill_template(template)
            urgency = random.choices(URGENCY_LEVELS, weights=URGENCY_WEIGHTS[category], k=1)[0]
            message = add_urgency_signal(message, urgency)
            rows.append((message, category, urgency))

    random.shuffle(rows)
    return rows


def main() -> None:
    rows = build_rows()
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    with open(OUT_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["message", "category", "urgency"])
        writer.writerows(rows)

    print(f"Dataset generated: {len(rows)} rows -> {OUT_PATH}")


if __name__ == "__main__":
    main()
