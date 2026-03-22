"""
Python-side calorie calculation and plan formatting.

Claude outputs a JSON plan (food names + grams). This module looks up
calorie/protein density from foods.json, calculates the numbers, and
formats the final display text.
"""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path

FOODS_FILE = Path(__file__).parent.parent / "foods.json"

_MEAL_ICON = {
    "desayuno": "🌅",
    "almuerzo": "☀️",
    "cena":     "🌙",
    "merienda": "🍎",
}
_MEAL_LABEL = {
    "desayuno": "DESAYUNO",
    "almuerzo": "ALMUERZO",
    "cena":     "CENA",
    "merienda": "MERIENDA",
}
_MEALS = ("desayuno", "almuerzo", "cena", "merienda")


def load_foods_db() -> dict:
    if not FOODS_FILE.exists():
        return {}
    with open(FOODS_FILE) as f:
        return json.load(f)


# ── Item-level helpers ────────────────────────────────────────────────────────

def _entry(item: dict, foods_db: dict) -> dict:
    return foods_db.get(item["alimento"], {})


def _resolve_grams(item: dict, grams_key: str, units_key: str, foods_db: dict) -> int:
    """Convert units → grams. Returns 0 for per-unit foods if only cal_per_unit is set."""
    if units_key in item:
        e = _entry(item, foods_db)
        return item[units_key] * e.get("grams_per_unit", 0)
    return item.get(grams_key, 0)


def _format_amount(item: dict, grams_key: str, units_key: str, foods_db: dict) -> str:
    """Return '2 huevos' / '1 arepa' for unit foods, or '150g' for gram foods."""
    if units_key in item:
        e = _entry(item, foods_db)
        unit = e.get("unit", "unidad")
        n = item[units_key]
        label = f"{unit}s" if n != 1 else unit
        return f"{n} {label}"
    return f"{item.get(grams_key, 0)}g"


def _item_cal(item: dict, grams: int, units: int, foods_db: dict) -> int:
    """
    Calculate calories for one item.
    Priority order:
      1. cal_per_unit in DB  (for unit-based items)
      2. cal_per_100g in DB  × grams/100
      3. cal_100g in item    × grams/100  (Claude-provided fallback)
    """
    e = _entry(item, foods_db)
    if units and "cal_per_unit" in e:
        return round(units * e["cal_per_unit"])
    cal_density = e.get("cal_per_100g") or float(item.get("cal_100g", 0))
    return round((grams / 100) * cal_density)


def _item_prot(item: dict, grams: int, units: int, foods_db: dict) -> float:
    """
    Calculate protein for one item.
    Priority order:
      1. protein_per_unit in DB
      2. protein_per_100g in DB  × grams/100
    """
    e = _entry(item, foods_db)
    if units and "protein_per_unit" in e:
        return units * e["protein_per_unit"]
    return (grams / 100) * e.get("protein_per_100g", 0.0)


# ── Single-person plan ────────────────────────────────────────────────────────

def format_single_plan(
    plan: dict,
    foods_db: dict,
    person_name: str,
    target: int,
    goal_desc: str,
    today: str,
    is_saturday: bool = False,
) -> tuple[str, str]:
    """Return (full_plan_text, wa_message)."""
    lines = [
        f"=== PLAN — {today.upper()} ===",
        f"Objetivo: {target} cal | {goal_desc}",
        "",
    ]

    meal_cals: dict[str, int] = {}
    total_prot = 0.0

    for meal in _MEALS:
        items = plan.get(meal, [])
        meal_total = 0
        cheat = " 🎉CHEAT" if meal == "cena" and is_saturday else ""
        meal_lines = []
        for item in items:
            u = item.get("unidades", 0)
            g = _resolve_grams(item, "gramos", "unidades", foods_db)
            cal = _item_cal(item, g, u, foods_db)
            meal_total += cal
            total_prot += _item_prot(item, g, u, foods_db)
            amount = _format_amount(item, "gramos", "unidades", foods_db)
            meal_lines.append(f"  • {item['alimento']} — {amount} — {cal} cal")
        meal_cals[meal] = meal_total
        lines.append(f"{_MEAL_ICON[meal]} {_MEAL_LABEL[meal]}{cheat} — {meal_total} cal")
        lines.extend(meal_lines)
        lines.append("")

    day_total = sum(meal_cals.values())
    frase = plan.get("frase", "")
    lines.append(f"TOTAL DEL DÍA: {day_total} cal")
    lines.append(f"MACROS: P~{round(total_prot)}g")
    if frase:
        lines.append(f"💪 {frase}")

    d, a, c, m = (meal_cals[k] for k in _MEALS)
    _d = date.today()
    _dias = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
    wa = (
        f"🌅{d}c ☀️{a}c 🌙{c}c 🍎{m}c\n"
        f"Total {day_total}cal — {frase}"
    )
    return "\n".join(lines), wa


# ── Dual-person plan ──────────────────────────────────────────────────────────

def format_dual_plan(
    plan: dict,
    foods_db: dict,
    p1_name: str,
    p1_target: int,
    p2_name: str,
    p2_target: int,
    today: str,
    is_saturday: bool = False,
) -> tuple[str, str]:
    """Return (full_plan_text, wa_message)."""
    lines = [
        f"=== PLAN — {today.upper()} ===",
        f"👨 {p1_name}: {p1_target} cal  |  👩 {p2_name}: {p2_target} cal",
        "",
    ]

    meal_cals_1: dict[str, int] = {}
    meal_cals_2: dict[str, int] = {}
    total_prot_1 = total_prot_2 = 0.0

    for meal in _MEALS:
        items = plan.get(meal, [])
        t1 = t2 = 0
        cheat = " 🎉CHEAT" if meal == "cena" and is_saturday else ""
        meal_lines = []
        for item in items:
            u1 = item.get("u1", 0)
            u2 = item.get("u2", 0)
            g1 = _resolve_grams(item, "g1", "u1", foods_db)
            g2 = _resolve_grams(item, "g2", "u2", foods_db)
            c1 = _item_cal(item, g1, u1, foods_db)
            c2 = _item_cal(item, g2, u2, foods_db)
            t1 += c1
            t2 += c2
            total_prot_1 += _item_prot(item, g1, u1, foods_db)
            total_prot_2 += _item_prot(item, g2, u2, foods_db)
            a1 = _format_amount(item, "g1", "u1", foods_db)
            a2 = _format_amount(item, "g2", "u2", foods_db)
            meal_lines.append(
                f"  • {item['alimento']} — 👨 [{a1}·{c1}cal] | 👩 [{a2}·{c2}cal]"
            )
        meal_cals_1[meal] = t1
        meal_cals_2[meal] = t2
        lines.append(
            f"{_MEAL_ICON[meal]} {_MEAL_LABEL[meal]}{cheat} — 👨 {t1}cal | 👩 {t2}cal"
        )
        lines.extend(meal_lines)
        lines.append("")

    day1 = sum(meal_cals_1.values())
    day2 = sum(meal_cals_2.values())
    frase = plan.get("frase", "")
    lines.append(f"TOTAL: 👨 {day1}cal | 👩 {day2}cal")
    lines.append(
        f"MACROS 👨 P~{round(total_prot_1)}g | 👩 P~{round(total_prot_2)}g"
    )
    if frase:
        lines.append(f"💪 {frase}")

    d1, a1, cin1, m1 = (meal_cals_1[k] for k in _MEALS)
    d2, a2, cin2, m2 = (meal_cals_2[k] for k in _MEALS)
    wa = (
        f"👨{p1_name} {day1}c 👩{p2_name} {day2}c\n"
        f"🌅{d1}/{d2} ☀️{a1}/{a2} 🌙{cin1}/{cin2} 🍎{m1}/{m2}\n"
        f"💪{frase}"
    )
    return "\n".join(lines), wa
