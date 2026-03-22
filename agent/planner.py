"""
Meal plan generation via the Claude Code CLI.

Claude outputs a JSON plan (food names + grams).
Python calculates calories from foods.json and formats the display.
"""

import json
import re
from datetime import date
from pathlib import Path

import anyio
from claude_agent_sdk import ClaudeAgentOptions, ResultMessage, query

from .calculator import ACTIVITY_DESCRIPTIONS, build_goal_description
from .meal_calculator import format_dual_plan, format_single_plan, load_foods_db

FOODS_FILE = Path(__file__).parent.parent / "foods.json"


def _load_food_inventory() -> str:
    """Load foods.json and format it as a compact table for the prompt."""
    if not FOODS_FILE.exists():
        return ""
    with open(FOODS_FILE) as f:
        db = json.load(f)
    lines = [f"  - {name}: {v['cal_per_100g']} cal/100g, {v['protein_per_100g']}g prot"
             for name, v in db.items()]
    return "INVENTARIO DISPONIBLE (prioriza estos alimentos):\n" + "\n".join(lines)


# Rotación semanal de proteínas para evitar repetición
# Índice = weekday() → 0=Lunes … 6=Domingo
PROTEIN_ROTATION = [
    "pasta boloñesa en el almuerzo (espagueti o penne con carne molida de res, tomate y especias)",  # Lunes
    "muslo de pollo (no pechuga a la plancha)",                                                       # Martes
    "arroz con mariscos en el almuerzo (camarones, mejillones o mezcla de mariscos con arroz)",       # Miércoles
    "costillas de cerdo San Luis o chicharrón",                                                       # Jueves
    "salmón o carne molida de res",                                                                   # Viernes
    "libre (cheat meal en la cena de hoy)",                                                           # Sábado
    "pechuga de pollo en preparación diferente a la plancha simple (ej: sudado, al horno, desmechado)", # Domingo
]


def _cheat_meal_rule(is_saturday: bool) -> str:
    if not is_saturday:
        return ""
    return (
        "\n🎉 HOY ES SÁBADO (CHEAT MEAL): La cena es libre, sin restricción calórica.\n"
    )


def _extract_json(text: str) -> dict | None:
    """Extract a JSON object from Claude's response, tolerating markdown fences."""
    text = text.strip()
    # Strip markdown code fences
    text = re.sub(r'^```(?:json)?\s*\n?', '', text)
    text = re.sub(r'\n?\s*```\s*$', '', text)
    text = text.strip()

    # Direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Find outermost { ... } block
    start = text.find('{')
    if start == -1:
        return None
    depth = 0
    for i, ch in enumerate(text[start:], start):
        if ch == '{':
            depth += 1
        elif ch == '}':
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(text[start:i + 1])
                except json.JSONDecodeError:
                    return None
    return None


def generate_meal_plan(config: dict, targets: dict, targets2: dict | None = None) -> tuple[str, str]:
    p     = config["profile"]
    prefs = config.get("preferences", {})
    _d    = date.today()

    _dias  = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
    _meses = ["enero", "febrero", "marzo", "abril", "mayo", "junio",
              "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]

    today = f"{_dias[_d.weekday()]}, {_d.day} de {_meses[_d.month - 1]} de {_d.year}"
    goal  = build_goal_description(config, targets)

    is_saturday = _d.weekday() == 5
    dual        = targets2 is not None

    extras = ""
    if prefs.get("dietary_restrictions"):
        extras += f"\nRestricciones: {', '.join(prefs['dietary_restrictions'])}"
    if prefs.get("cuisine"):
        extras += f"\nCocina: {', '.join(prefs['cuisine'])}"

    food_inventory = _load_food_inventory()

    # Build a compact list of unit-based foods to show Claude
    foods_db_hint = load_foods_db()
    unit_foods = [name for name, v in foods_db_hint.items() if "grams_per_unit" in v]
    unit_foods_str = ", ".join(unit_foods)

    if dual:
        p2      = config["profile2"]
        config2 = {**config, "profile": p2, "goal": config["goal2"]}
        goal2   = build_goal_description(config2, targets2)
        contexto = (
            f"👨 {p['name']}: {p['weight_kg']}kg {p['height_cm']}cm {p['age']}a "
            f"{ACTIVITY_DESCRIPTIONS[p['activity_level']]} → {targets['target']} cal/día ({goal})\n"
            f"👩 {p2['name']}: {p2['weight_kg']}kg {p2['height_cm']}cm {p2['age']}a "
            f"{ACTIVITY_DESCRIPTIONS[p2['activity_level']]} → {targets2['target']} cal/día ({goal2}){extras}"
        )
        schema = json.dumps({
            "desayuno": [
                {"alimento": "arepa de maíz", "u1": 1, "u2": 1},
                {"alimento": "huevo entero", "u1": 2, "u2": 1},
                {"alimento": "tomate", "g1": 80, "g2": 60, "cal_100g": 18},
            ],
            "almuerzo": [{"alimento": "arroz blanco", "g1": 200, "g2": 160}],
            "cena":     [{"alimento": "pechuga de pollo", "g1": 180, "g2": 140}],
            "merienda": [{"alimento": "banano", "u1": 1, "u2": 1}],
            "frase": "Frase motivacional breve",
        }, ensure_ascii=False, indent=2)
        items_rule = (
            f"Ítems: desayuno 3, almuerzo 4, cena 3, merienda 2. "
            f"g1={p['name']}, g2={p2['name']}. "
            f"u1={p['name']}, u2={p2['name']} (para alimentos contables)."
        )
    else:
        contexto = (
            f"{p['name']}: {p['weight_kg']}kg {p['height_cm']}cm {p['age']}a "
            f"{ACTIVITY_DESCRIPTIONS[p['activity_level']]} → {targets['target']} cal/día ({goal}){extras}"
        )
        schema = json.dumps({
            "desayuno": [
                {"alimento": "arepa de maíz", "unidades": 1},
                {"alimento": "huevo entero", "unidades": 2},
                {"alimento": "tomate", "gramos": 80, "cal_100g": 18},
            ],
            "almuerzo": [{"alimento": "arroz blanco", "gramos": 200}],
            "cena":     [{"alimento": "pechuga de pollo", "gramos": 180}],
            "merienda": [{"alimento": "banano", "unidades": 1}],
            "frase": "Frase motivacional breve",
        }, ensure_ascii=False, indent=2)
        items_rule = "Ítems: desayuno 3, almuerzo 4, cena 3, merienda 2."

    prompt = f"""Plan de alimentación — {today}.
{contexto}

{food_inventory}

REGLAS: gramos cocidos. Prioriza los alimentos del inventario.
Completa con alimentos colombianos (papa, plátano, yuca, verduras, frutas). Sin quinoa/kale. Salmón solo viernes.
Para alimentos fuera del inventario incluye "cal_100g" en el ítem JSON.
Alimentos contables (usa "unidades"/"u1"/"u2" en lugar de gramos): {unit_foods_str}.
PROTEÍNA DEL DÍA (obligatorio): {PROTEIN_ROTATION[_d.weekday()]}{_cheat_meal_rule(is_saturday)}
{items_rule}

Responde SOLO con JSON válido, sin markdown ni texto adicional:
{schema}"""

    print("  Generando tu plan de alimentación...")

    result: list[str] = []

    async def _run() -> None:
        async for message in query(
            prompt=prompt,
            options=ClaudeAgentOptions(allowed_tools=[]),
        ):
            if isinstance(message, ResultMessage):
                result.append(message.result)

    anyio.run(_run)
    raw = result[0] if result else ""

    plan = _extract_json(raw)
    if plan is None:
        # Fallback: return raw response as-is
        _dias_short = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
        fallback_wa = (
            f"🥗 Plan del {_dias_short[_d.weekday()]} {_d.day}/{_d.month} listo.\n"
            f"Abre la app para ver el detalle."
        )
        return raw.strip(), fallback_wa

    foods_db = load_foods_db()

    if dual:
        p2 = config["profile2"]
        return format_dual_plan(
            plan, foods_db,
            p["name"], targets["target"],
            p2["name"], targets2["target"],
            today, is_saturday,
        )
    else:
        return format_single_plan(
            plan, foods_db,
            p["name"], targets["target"], goal,
            today, is_saturday,
        )
