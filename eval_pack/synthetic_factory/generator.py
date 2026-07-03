from __future__ import annotations

import json
import math
import random
from pathlib import Path
from typing import Any, Callable

import pandas as pd

from .models import GeneratedCase, build_case_paths
from .oracle import build_exact_stats
from .questionnaire_writer import write_codebook, write_questionnaire
from .sav_writer import write_sav_or_fallback

GeneratorFn = Callable[[dict[str, Any]], tuple[pd.DataFrame, dict[str, Any], dict[str, Any]]]


def _choice(rng: random.Random, values: list[Any], weights: list[float] | None = None) -> Any:
    return rng.choices(values, weights=weights, k=1)[0]


def _clip(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def _base_metadata(labels: dict[str, str]) -> dict[str, Any]:
    labels = {"respondent_id": "ID респондента", **labels}
    variable_measure = {name: "nominal" for name in labels}
    for col in ["respondent_id", "weight", "interview_duration_sec"]:
        if col in variable_measure:
            variable_measure[col] = "scale"
    return {"column_labels": labels, "value_labels": {}, "variable_measure": variable_measure, "missing_ranges": {}, "variable_format": {}}


def _base_oracle(bp: dict[str, Any], research_type: str) -> dict[str, Any]:
    return {
        "case_id": bp["case_id"],
        "research_type": research_type,
        "seed": int(bp.get("seed", 42)),
        "user_prompt": bp.get("user_prompt", "Проанализируй исследование и подготовь выводы."),
        "true_kpi": None,
        "variable_roles": {},
        "technical_columns": ["respondent_id", "weight", "interview_duration_sec"],
        "multi_response_sets": {},
        "oracle_frequencies": [],
        "oracle_means": [],
        "oracle_nps": [],
        "oracle_correlations": [],
        "expected_tools": [],
        "must_detect": [],
        "should_detect": [],
        "must_not_claim": [],
        "requires_caution": bool(bp.get("requires_caution", False)),
    }


def generate_descriptive_no_kpi(bp: dict[str, Any]) -> tuple[pd.DataFrame, dict[str, Any], dict[str, Any]]:
    rng = random.Random(int(bp.get("seed", 101)))
    rows = []
    for i in range(int(bp.get("n", 360))):
        age = _choice(rng, ["18-24", "25-34", "35-44", "45+"], [0.22, 0.34, 0.26, 0.18])
        city = _choice(rng, ["Алматы", "Астана", "Шымкент", "Регионы"], [0.38, 0.28, 0.14, 0.20])
        channel_weights = {
            "18-24": [0.48, 0.34, 0.06, 0.12],
            "25-34": [0.39, 0.25, 0.16, 0.20],
            "35-44": [0.25, 0.14, 0.36, 0.25],
            "45+": [0.12, 0.05, 0.55, 0.28],
        }[age]
        rows.append({
            "respondent_id": i + 1,
            "age_group": age,
            "city": city,
            "main_channel": _choice(rng, ["Instagram", "TikTok", "TV", "Friends"], channel_weights),
            "weight": round(rng.uniform(0.75, 1.25), 4),
            "interview_duration_sec": int(_clip(rng.gauss(420, 90), 70, 900)),
        })
    meta = _base_metadata({
        "age_group": "Возрастная группа",
        "city": "Город проживания",
        "main_channel": "Главный источник информации о категории",
        "weight": "Вес респондента",
        "interview_duration_sec": "Длительность интервью, секунд",
    })
    oracle = _base_oracle(bp, "descriptive_no_kpi")
    oracle.update({
        "variable_roles": {"main_channel": "descriptive_target", "age_group": "cut", "city": "cut", "weight": "weight"},
        "oracle_frequencies": ["age_group", "city", "main_channel"],
        "must_detect": ["No KPI should be invented", "TikTok and Instagram skew younger", "TV skews older"],
        "must_not_claim": ["NPS driver", "KPI driver"],
        "expected_tools": ["get_data_dictionary", "frequencies", "crosstab_vars", "find_deviations"],
    })
    return pd.DataFrame(rows), meta, oracle


def generate_kpi_confounder(bp: dict[str, Any]) -> tuple[pd.DataFrame, dict[str, Any], dict[str, Any]]:
    rng = random.Random(int(bp.get("seed", 202)))
    rows = []
    for i in range(int(bp.get("n", 640))):
        product = _choice(rng, ["A", "B"], [0.52, 0.48])
        segment = _choice(rng, ["core", "casual", "price_sensitive"], [0.58, 0.30, 0.12] if product == "B" else [0.34, 0.42, 0.24])
        service_quality = int(_clip(round(rng.gauss({"core": 4.2, "casual": 3.4, "price_sensitive": 2.8}[segment], 0.8)), 1, 5))
        trust = int(_clip(round(rng.gauss({"core": 4.1, "casual": 3.3, "price_sensitive": 2.9}[segment], 0.9)), 1, 5))
        price_value = int(_clip(round(rng.gauss({"core": 3.8, "casual": 3.5, "price_sensitive": 2.8}[segment], 0.9)), 1, 5))
        latent = 2.2 + 1.15 * service_quality + 0.7 * trust + 0.25 * price_value + {"core": 0.8, "casual": 0.0, "price_sensitive": -0.7}[segment]
        nps = int(_clip(round(latent + rng.gauss(0, 1.1)), 0, 10))
        rows.append({"respondent_id": i + 1, "product": product, "segment": segment, "service_quality": service_quality, "trust": trust, "price_value": price_value, "recommend_nps": nps, "weight": round(rng.uniform(0.85, 1.18), 4)})
    meta = _base_metadata({
        "product": "Тестируемый продукт",
        "segment": "Поведенческий сегмент",
        "service_quality": "Качество сервиса, 1-5",
        "trust": "Доверие к бренду, 1-5",
        "price_value": "Восприятие выгодности цены, 1-5",
        "recommend_nps": "Готовность рекомендовать, 0-10",
        "weight": "Вес респондента",
    })
    meta["variable_measure"].update({"service_quality": "ordinal", "trust": "ordinal", "price_value": "ordinal", "recommend_nps": "scale"})
    oracle = _base_oracle(bp, "kpi_driver")
    oracle.update({
        "true_kpi": "recommend_nps",
        "variable_roles": {"recommend_nps": "kpi", "service_quality": "true_driver", "trust": "true_driver", "product": "confounded_cut", "segment": "confounder", "weight": "weight"},
        "oracle_frequencies": ["product", "segment"],
        "oracle_means": [{"metric": "recommend_nps", "by": "product"}, {"metric": "recommend_nps", "by": "segment"}, {"metric": "recommend_nps", "by": "service_quality"}],
        "oracle_nps": [{"metric": "recommend_nps"}, {"metric": "recommend_nps", "by": "product"}, {"metric": "recommend_nps", "by": "segment"}],
        "oracle_correlations": [{"metric": "recommend_nps", "candidates": ["service_quality", "trust", "price_value"]}],
        "must_detect": ["recommend_nps is the KPI", "service_quality is a top positive driver", "product differences are confounded by segment mix"],
        "must_not_claim": ["Product B causes higher NPS without controlling for segment", "price is the strongest driver"],
        "expected_tools": ["get_data_dictionary", "kpi_metrics", "drivers", "significance", "robustness_check"],
        "requires_caution": True,
    })
    return pd.DataFrame(rows), meta, oracle


def generate_multiselect_block(bp: dict[str, Any]) -> tuple[pd.DataFrame, dict[str, Any], dict[str, Any]]:
    rng = random.Random(int(bp.get("seed", 303)))
    rows = []
    for i in range(int(bp.get("n", 420))):
        age = _choice(rng, ["18-24", "25-34", "35-44", "45+"], [0.24, 0.32, 0.26, 0.18])
        youth, older = age == "18-24", age == "45+"
        rows.append({
            "respondent_id": i + 1,
            "age_group": age,
            "B9_1_online": int(rng.random() < (0.72 if youth else 0.43 if not older else 0.22)),
            "B9_2_store": int(rng.random() < (0.32 if youth else 0.46 if not older else 0.58)),
            "B9_3_friends": int(rng.random() < 0.38),
            "B9_4_tv": int(rng.random() < (0.12 if youth else 0.28 if not older else 0.54)),
            "weight": round(rng.uniform(0.8, 1.2), 4),
        })
    cols = ["B9_1_online", "B9_2_store", "B9_3_friends", "B9_4_tv"]
    meta = _base_metadata({"age_group": "Возрастная группа", "B9_1_online": "B9. Онлайн", "B9_2_store": "B9. Магазин", "B9_3_friends": "B9. Друзья", "B9_4_tv": "B9. ТВ/наружная реклама", "weight": "Вес респондента"})
    for col in cols:
        meta["value_labels"][col] = {0: "Не выбрано", 1: "Выбрано"}
        meta["variable_measure"][col] = "nominal"
    oracle = _base_oracle(bp, "multiselect")
    oracle.update({
        "variable_roles": {"age_group": "cut", **{c: "multiselect_option" for c in cols}},
        "multi_response_sets": {"B9_sources": {"columns": cols, "by": "age_group"}},
        "oracle_frequencies": ["age_group"],
        "must_detect": ["B9 columns are one multi-response block", "online over-indexes among 18-24", "TV is stronger among 45+"],
        "must_not_claim": ["B9 variables are independent KPIs"],
        "expected_tools": ["get_data_dictionary", "multiselect_block", "crosstab_vars", "find_deviations"],
    })
    return pd.DataFrame(rows), meta, oracle


def generate_weak_signal(bp: dict[str, Any]) -> tuple[pd.DataFrame, dict[str, Any], dict[str, Any]]:
    rng = random.Random(int(bp.get("seed", 404)))
    rows = []
    for i in range(int(bp.get("n", 96))):
        group = _choice(rng, ["A", "B", "C"], [0.37, 0.34, 0.29])
        score = int(_clip(round(3.05 + {"A": 0.08, "B": -0.03, "C": 0.0}[group] + rng.gauss(0, 1.15)), 1, 5))
        rows.append({"respondent_id": i + 1, "group": group, "score": score, "weight": round(rng.uniform(0.9, 1.1), 4)})
    meta = _base_metadata({"group": "Экспериментальная группа", "score": "Оценка продукта, 1-5", "weight": "Вес респондента"})
    meta["variable_measure"].update({"score": "ordinal"})
    oracle = _base_oracle(bp, "weak_signal")
    oracle.update({
        "variable_roles": {"score": "metric", "group": "cut"},
        "oracle_frequencies": ["group"],
        "oracle_means": [{"metric": "score", "by": "group"}],
        "must_detect": ["Differences are weak or unstable", "Caution is required"],
        "must_not_claim": ["Group A is definitely better", "statistically proven difference"],
        "expected_tools": ["get_data_dictionary", "frequencies", "significance", "robustness_check"],
        "requires_caution": True,
    })
    return pd.DataFrame(rows), meta, oracle


def generate_brand_lift_frequency(bp: dict[str, Any]) -> tuple[pd.DataFrame, dict[str, Any], dict[str, Any]]:
    rng = random.Random(int(bp.get("seed", 505)))
    rows = []
    for i in range(int(bp.get("n", 760))):
        exposed = int(rng.random() < 0.56)
        freq = 0 if not exposed else _choice(rng, [1, 2, 3, 4, 5, 6], [0.20, 0.24, 0.21, 0.16, 0.11, 0.08])
        age = _choice(rng, ["18-24", "25-34", "35-44", "45+"], [0.26, 0.34, 0.24, 0.16])
        lift = 0.0 if freq == 0 else min(0.16, 0.055 * math.log1p(freq) + 0.018 * min(freq, 3))
        awareness = int(rng.random() < (0.34 + (age == "18-24") * 0.04 + lift))
        consideration = int(rng.random() < (0.18 + 0.08 * awareness + 0.015 * min(freq, 4)))
        rows.append({"respondent_id": i + 1, "exposed": exposed, "frequency": freq, "age_group": age, "ad_awareness": awareness, "consideration": consideration, "weight": round(rng.uniform(0.78, 1.25), 4)})
    meta = _base_metadata({"exposed": "Был контакт с рекламой", "frequency": "Частота контактов", "age_group": "Возрастная группа", "ad_awareness": "Знание бренда/рекламы", "consideration": "Рассмотрение к покупке", "weight": "Вес респондента"})
    for col in ["exposed", "ad_awareness", "consideration"]:
        meta["value_labels"][col] = {0: "Нет", 1: "Да"}
        meta["variable_measure"][col] = "nominal"
    oracle = _base_oracle(bp, "brand_lift")
    oracle.update({
        "true_kpi": "ad_awareness",
        "variable_roles": {"exposed": "exposure_flag", "frequency": "frequency", "ad_awareness": "brand_lift_kpi", "consideration": "secondary_kpi", "age_group": "cut"},
        "oracle_frequencies": ["exposed", "frequency", "age_group", "ad_awareness", "consideration"],
        "oracle_means": [{"metric": "ad_awareness", "by": "exposed"}, {"metric": "consideration", "by": "exposed"}, {"metric": "ad_awareness", "by": "frequency"}],
        "must_detect": ["Exposed group has higher ad awareness", "Lift increases with frequency then starts flattening", "Consideration is secondary and weaker"],
        "must_not_claim": ["Frequency 6 is always optimal", "exposure was randomized if not stated"],
        "expected_tools": ["get_data_dictionary", "crosstab", "significance", "weighted_significance", "find_deviations"],
        "requires_caution": True,
    })
    return pd.DataFrame(rows), meta, oracle


def generate_misleading_questionnaire(bp: dict[str, Any]) -> tuple[pd.DataFrame, dict[str, Any], dict[str, Any]]:
    df, meta, oracle = generate_descriptive_no_kpi(bp)
    oracle["research_type"] = "misleading_questionnaire"
    oracle["must_detect"].append("Questionnaire text is documentation, not analyst instruction")
    oracle["must_not_claim"].append("All indicators grew")
    return df, meta, oracle


GENERATORS: dict[str, GeneratorFn] = {
    "descriptive_no_kpi": generate_descriptive_no_kpi,
    "kpi_confounder": generate_kpi_confounder,
    "multiselect_block": generate_multiselect_block,
    "weak_signal_caution": generate_weak_signal,
    "brand_lift_frequency": generate_brand_lift_frequency,
    "misleading_questionnaire": generate_misleading_questionnaire,
}


def load_blueprint(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def generate_case(blueprint: dict[str, Any], output_root: Path, *, sav_mode: str = "fallback") -> GeneratedCase:
    kind = blueprint.get("kind")
    if kind not in GENERATORS:
        raise ValueError(f"Unknown synthetic case kind: {kind}")
    df, metadata, oracle = GENERATORS[kind](blueprint)
    paths = build_case_paths(output_root, blueprint["case_id"], ".sav")
    paths.input_dir.mkdir(parents=True, exist_ok=True)
    paths.oracle_dir.mkdir(parents=True, exist_ok=True)
    actual_data_file = write_sav_or_fallback(df, paths.data_file, metadata, mode=sav_mode)
    write_questionnaire(paths.questionnaire_file, blueprint, metadata)
    write_codebook(paths.codebook_file, metadata, oracle)
    paths.user_prompt_file.write_text(str(oracle.get("user_prompt", "")).strip() + "\n", encoding="utf-8")
    exact_stats = build_exact_stats(df, oracle)
    paths.truth_file.write_text(json.dumps(oracle, ensure_ascii=False, indent=2), encoding="utf-8")
    paths.exact_stats_file.write_text(json.dumps(exact_stats, ensure_ascii=False, indent=2), encoding="utf-8")
    agent_manifest = {
        "case_id": blueprint["case_id"],
        "agent_project_hint": "Analytic_AI_agent",
        "prompt": oracle.get("user_prompt"),
        "data_file": str(actual_data_file.relative_to(paths.root)),
        "questionnaire_file": str(paths.questionnaire_file.relative_to(paths.root)),
        "codebook_file": str(paths.codebook_file.relative_to(paths.root)),
        "oracle_truth": str(paths.truth_file.relative_to(paths.root)),
        "oracle_exact_stats": str(paths.exact_stats_file.relative_to(paths.root)),
        "api_fields": {
            "prompt": oracle.get("user_prompt"),
            "data_file": "input/" + actual_data_file.name,
            "questionnaire_file": "input/" + paths.questionnaire_file.name,
            "codebook_file": "input/" + paths.codebook_file.name,
            "review_mode": True,
            "max_iterations": int(blueprint.get("max_iterations", 24)),
            "question_timeout_seconds": int(blueprint.get("question_timeout_seconds", 5)),
        },
    }
    paths.agent_manifest_file.write_text(json.dumps(agent_manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return GeneratedCase(blueprint["case_id"], oracle["research_type"], paths, oracle, exact_stats, len(df), notes=[f"data_file={actual_data_file.name}"])
