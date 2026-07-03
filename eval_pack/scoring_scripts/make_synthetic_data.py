#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import random
from pathlib import Path


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def descriptive_no_kpi(out: Path) -> None:
    rng = random.Random(42)
    rows = []
    for i in range(180):
        age = rng.choice(["18-24", "25-34", "35-44", "45+"])
        city = rng.choice(["Алматы", "Астана", "Шымкент"])
        channel = rng.choices(["Instagram", "TikTok", "TV", "Friends"], [36, 29, 20, 15])[0]
        rows.append({"id": i + 1, "age_group": age, "city": city, "main_channel": channel, "weight": round(rng.uniform(0.8, 1.2), 3)})
    write_csv(out / "descriptive_no_kpi.csv", rows)
    (out / "descriptive_no_kpi_questionnaire.txt").write_text("Q1 age_group: Возраст\nQ2 city: Город\nQ3 main_channel: Главный источник информации\n", encoding="utf-8")


def kpi_confounder(out: Path) -> None:
    rng = random.Random(7)
    rows = []
    for i in range(240):
        segment = rng.choices(["core", "casual", "price_sensitive"], [45, 35, 20])[0]
        product = rng.choice(["A", "B"])
        service = rng.randint(1, 5)
        price = rng.randint(1, 5)
        base = 5 + (segment == "core") * 1.4 + (service >= 4) * 1.8 - (price <= 2) * 0.9
        nps = max(0, min(10, round(base + rng.gauss(0, 1.2))))
        rows.append({"id": i + 1, "segment": segment, "product": product, "service_quality": service, "price_value": price, "recommend_nps": nps})
    write_csv(out / "kpi_confounder.csv", rows)
    (out / "kpi_confounder_questionnaire.txt").write_text("Q1 segment: Сегмент\nQ2 product: Продукт\nQ3 service_quality: Качество сервиса 1-5\nQ4 price_value: Выгодность цены 1-5\nQ5 recommend_nps: Готовность рекомендовать 0-10\n", encoding="utf-8")


def weak_signal(out: Path) -> None:
    rng = random.Random(99)
    rows = []
    for i in range(90):
        group = rng.choice(["A", "B", "C"])
        score = max(1, min(5, round(3 + rng.gauss(0, 1.1))))
        rows.append({"id": i + 1, "group": group, "score": score, "comment": rng.choice(["ok", "normal", "hard to say"])})
    write_csv(out / "weak_signal.csv", rows)
    (out / "weak_signal_questionnaire.txt").write_text("Q1 group: Группа\nQ2 score: Оценка 1-5\nQ3 comment: Комментарий\n", encoding="utf-8")


def multiselect(out: Path) -> None:
    rng = random.Random(123)
    rows = []
    for i in range(160):
        age = rng.choice(["18-24", "25-34", "35+"])
        rows.append({
            "id": i + 1,
            "age_group": age,
            "B9_1": int(rng.random() < (0.62 if age == "18-24" else 0.38)),
            "B9_2": int(rng.random() < 0.41),
            "B9_3": int(rng.random() < (0.25 if age == "18-24" else 0.50)),
            "B9_4": int(rng.random() < 0.18),
        })
    write_csv(out / "multiselect_block.csv", rows)
    (out / "multiselect_block_questionnaire.txt").write_text("Q1 age_group: Возраст\nB9_1: Выбирает онлайн\nB9_2: Выбирает магазин\nB9_3: Выбирает рекомендации\nB9_4: Выбирает наружную рекламу\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="eval_pack/test_datasets/generated")
    args = parser.parse_args()
    out = Path(args.out)
    descriptive_no_kpi(out)
    kpi_confounder(out)
    weak_signal(out)
    multiselect(out)
    print(f"synthetic datasets written to {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
