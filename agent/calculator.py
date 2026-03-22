"""
BMR / TDEE calculations and goal-based calorie targeting.

Formulas used:
  BMR  — Mifflin-St Jeor equation
  TDEE — BMR × activity multiplier
  Target — TDEE ± safe daily deficit/surplus toward the user's goal
"""

ACTIVITY_MULTIPLIERS: dict[str, float] = {
    "sedentary":   1.2,
    "light":       1.375,
    "moderate":    1.55,
    "active":      1.725,
    "very_active": 1.9,
}

ACTIVITY_DESCRIPTIONS: dict[str, str] = {
    "sedentary":   "Little or no exercise",
    "light":       "Light exercise 1-3 days/week",
    "moderate":    "Moderate exercise 3-5 days/week",
    "active":      "Hard exercise 6-7 days/week",
    "very_active": "Very hard exercise / physical job",
}

# Safety caps to avoid extreme deficits/surpluses
MAX_DAILY_DEFICIT  = 1000  # cal — ~0.9 kg/week loss
MAX_DAILY_SURPLUS  =  500  # cal — ~0.45 kg/week gain

# Calories stored in 1 kg of body fat
KCAL_PER_KG = 7700


def calculate_bmr(weight_kg: float, height_cm: float, age: int, gender: str) -> float:
    """Mifflin-St Jeor Equation (most accurate for the general population)."""
    base = 10 * weight_kg + 6.25 * height_cm - 5 * age
    return base + 5 if gender.lower() == "male" else base - 161


def calculate_targets(config: dict) -> dict:
    """
    Return a dict with:
      bmr    — base metabolic rate (calories burned at rest)
      tdee   — total daily energy expenditure (maintenance calories)
      target — daily calorie goal adjusted for the user's goal
    """
    p = config["profile"]
    g = config["goal"]

    bmr  = calculate_bmr(p["weight_kg"], p["height_cm"], p["age"], p["gender"])
    tdee = bmr * ACTIVITY_MULTIPLIERS[p["activity_level"]]

    if g["type"] == "lose_weight":
        kg_to_lose = p["weight_kg"] - g["target_weight_kg"]
        daily_deficit = (kg_to_lose * KCAL_PER_KG) / (g["timeframe_weeks"] * 7)
        daily_deficit = min(daily_deficit, MAX_DAILY_DEFICIT)
        target = tdee - daily_deficit

    elif g["type"] == "gain_weight":
        kg_to_gain = g["target_weight_kg"] - p["weight_kg"]
        daily_surplus = (kg_to_gain * KCAL_PER_KG) / (g["timeframe_weeks"] * 7)
        daily_surplus = min(daily_surplus, MAX_DAILY_SURPLUS)
        target = tdee + daily_surplus

    else:  # maintain
        target = tdee

    return {
        "bmr":    round(bmr),
        "tdee":   round(tdee),
        "target": round(target),
    }


def build_goal_description(config: dict, targets: dict) -> str:
    """Resumen legible de la meta y el ajuste calórico diario."""
    g = config["goal"]
    p = config["profile"]

    if g["type"] == "lose_weight":
        kg      = p["weight_kg"] - g["target_weight_kg"]
        deficit = targets["tdee"] - targets["target"]
        return f"Perder {kg:.1f} kg en {g['timeframe_weeks']} semanas (déficit: {deficit} cal/día)"

    if g["type"] == "gain_weight":
        kg      = g["target_weight_kg"] - p["weight_kg"]
        surplus = targets["target"] - targets["tdee"]
        return f"Ganar {kg:.1f} kg en {g['timeframe_weeks']} semanas (superávit: {surplus} cal/día)"

    return "Mantener peso actual"
