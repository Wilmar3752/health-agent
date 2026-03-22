"""
Interactive setup wizard.

Collects the user's profile, goal, dietary preferences, and optional
WhatsApp credentials, then writes config.json to the project root.
"""

import json
from pathlib import Path

from .calculator import (
    ACTIVITY_DESCRIPTIONS,
    ACTIVITY_MULTIPLIERS,
    build_goal_description,
    calculate_targets,
)
from .notifier import send_whatsapp

PROJECT_ROOT = Path(__file__).parent.parent
CONFIG_FILE  = PROJECT_ROOT / "config.json"


# ── Helpers ───────────────────────────────────────────────────────────────────

def ask(label: str, default: str = "") -> str:
    suffix = f" [{default}]" if default else ""
    value  = input(f"  {label}{suffix}: ").strip()
    return value or default


def ask_float(label: str) -> float:
    while True:
        raw = ask(label)
        try:
            return float(raw)
        except ValueError:
            print("  Ingresa un número (ej: 75.5)")


def ask_int(label: str) -> int:
    while True:
        raw = ask(label)
        try:
            return int(raw)
        except ValueError:
            print("  Ingresa un número entero (ej: 30)")


def section(title: str) -> None:
    print(f"\n  {title}")
    print("  " + "─" * 32)


# ── Wizard ────────────────────────────────────────────────────────────────────

def _ask_profile_and_goal(label: str) -> tuple[dict, dict]:
    """Reusable block: ask for profile + goal for one person."""
    section(f"Perfil — {label}")

    name   = ask("Nombre", label)
    weight = ask_float("Peso actual (kg)")
    height = ask_float("Talla (cm)")
    age    = ask_int("Edad")

    while True:
        gender = ask("Sexo (male/female)").lower()
        if gender in ("male", "female"):
            break
        print("  Ingresa 'male' o 'female'")

    levels = list(ACTIVITY_MULTIPLIERS.keys())
    print()
    print("  Niveles de actividad:")
    for i, lvl in enumerate(levels, 1):
        print(f"    {i}. {ACTIVITY_DESCRIPTIONS[lvl]}")

    while True:
        c = ask("Nivel de actividad (1-5)")
        if c.isdigit() and 1 <= int(c) <= 5:
            activity_level = levels[int(c) - 1]
            break
        print("  Ingresa un número del 1 al 5")

    profile = {
        "name":           name,
        "weight_kg":      weight,
        "height_cm":      height,
        "age":            age,
        "gender":         gender,
        "activity_level": activity_level,
    }

    section(f"Meta — {label}")
    print("    1. Perder peso")
    print("    2. Ganar peso")
    print("    3. Mantener peso")

    while True:
        c = ask("Meta (1-3)")
        if c in ("1", "2", "3"):
            goal_type = {"1": "lose_weight", "2": "gain_weight", "3": "maintain"}[c]
            break
        print("  Ingresa 1, 2 o 3")

    goal: dict = {"type": goal_type}

    if goal_type in ("lose_weight", "gain_weight"):
        verb          = "bajar a" if goal_type == "lose_weight" else "subir a"
        target_weight = ask_float(f"Peso objetivo a {verb} (kg)")
        timeframe     = ask_int("Plazo (semanas)")
        goal["target_weight_kg"] = target_weight
        goal["timeframe_weeks"]  = timeframe

    return profile, goal


def run_setup() -> None:
    print()
    print("  ╔══════════════════════════════════╗")
    print("  ║   Health Agent — Setup Wizard    ║")
    print("  ╚══════════════════════════════════╝")

    # ── Persona 1 ─────────────────────────────────────────────────────────────
    profile1, goal1 = _ask_profile_and_goal("Persona 1")
    config: dict = {"profile": profile1, "goal": goal1}

    # ── Persona 2 (opcional) ──────────────────────────────────────────────────
    print()
    if ask("¿Agregar una segunda persona al plan? (y/n)", "n").lower() == "y":
        profile2, goal2 = _ask_profile_and_goal("Persona 2")
        config["profile2"] = profile2
        config["goal2"]    = goal2

    # ── Preferencias ──────────────────────────────────────────────────────────
    section("Preferencias alimentarias  (Enter para omitir)")

    restrictions = ask("Restricciones (ej: vegetariano, sin gluten)")
    cuisine      = ask("Preferencias de cocina (ej: colombiana, mediterránea)")

    config["preferences"] = {
        "dietary_restrictions": [r.strip() for r in restrictions.split(",") if r.strip()],
        "cuisine":              [c.strip() for c in cuisine.split(",") if c.strip()],
    }

    # ── WhatsApp ──────────────────────────────────────────────────────────────
    section("Notificaciones WhatsApp  (gratis con CallMeBot)")
    print("  Activación única:")
    print("  1. Guarda +34 644 50 10 99 como contacto en WhatsApp")
    print('  2. Envíale: "I allow callmebot to send me messages"')
    print("  3. Recibirás tu API key en segundos")
    print()

    if ask("¿Configurar WhatsApp? (y/n)", "n").lower() == "y":
        phone  = ask("Tu número de WhatsApp (ej: +573001234567)")
        apikey = ask("API key de CallMeBot")
        config["notification"] = {
            "whatsapp_phone":  phone,
            "whatsapp_apikey": apikey,
        }
        if ask("¿Enviar mensaje de prueba ahora? (y/n)", "y").lower() == "y":
            targets  = calculate_targets(config)
            test_msg = (
                f"✅ Health Agent conectado. "
                f"Objetivo diario: {targets['target']} cal. "
                f"Meta: {build_goal_description(config, targets)}"
            )
            if send_whatsapp(config, test_msg):
                print("  ✅ Mensaje enviado. Revisa tu WhatsApp.")
            else:
                print("  ❌ Falló — revisa tu número y API key.")
    else:
        config["notification"] = {}

    # ── Guardar y mostrar resumen ──────────────────────────────────────────────
    CONFIG_FILE.write_text(json.dumps(config, indent=2))

    print()
    print("  ╔══════════════════════════════════╗")
    print("  ║           Resumen                ║")
    print("  ╚══════════════════════════════════╝")

    def _print_stats(label: str, cfg: dict) -> None:
        t = calculate_targets(cfg)
        g = cfg["goal"]
        print(f"\n  {label}")
        print(f"  TMB (base):         {t['bmr']:>5} cal/día")
        print(f"  TDEE (mant.):       {t['tdee']:>5} cal/día")
        print(f"  Objetivo diario:    {t['target']:>5} cal/día")
        if g["type"] == "lose_weight":
            deficit   = t["tdee"] - t["target"]
            weeks     = g["timeframe_weeks"]
            projected = (deficit * weeks * 7) / 7700
            print(f"  Déficit diario:     {deficit:>5} cal")
            print(f"  Pérdida estimada:   {projected:.1f} kg en {weeks} semanas")
        elif g["type"] == "gain_weight":
            surplus   = t["target"] - t["tdee"]
            weeks     = g["timeframe_weeks"]
            projected = (surplus * weeks * 7) / 7700
            print(f"  Superávit diario:   {surplus:>5} cal")
            print(f"  Ganancia estimada:  {projected:.1f} kg en {weeks} semanas")

    _print_stats(f"👨 {config['profile']['name']}", config)
    if "profile2" in config:
        config2 = {**config, "profile": config["profile2"], "goal": config["goal2"]}
        _print_stats(f"👩 {config['profile2']['name']}", config2)

    print()
    print(f"  Config guardada → config.json")
    print()
    print("  Próximos pasos:")
    print("    python health_agent.py --run")
    print()
    root = PROJECT_ROOT.resolve()
    print("  Cron diario a las 8 AM (ejecuta: crontab -e):")
    print(f"    3 8 * * *  cd {root} && python health_agent.py --run >> logs/health_agent.log 2>&1")
    print()
