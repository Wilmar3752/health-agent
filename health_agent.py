#!/usr/bin/env python3
"""
Health Agent — CLI entry point.

Usage:
    python health_agent.py --setup    # first-time setup wizard
    python health_agent.py --run      # generate today's meal plan
"""

import argparse
import json
import sys
from pathlib import Path

CONFIG_FILE = Path(__file__).parent / "config.json"


def run_agent() -> None:
    if not CONFIG_FILE.exists():
        print("No config found. Run first:\n  python health_agent.py --setup")
        sys.exit(1)

    with open(CONFIG_FILE) as f:
        config = json.load(f)

    from agent.calculator import calculate_targets
    from agent.planner    import generate_meal_plan
    from agent.notifier   import send_whatsapp

    targets = calculate_targets(config)

    dual = "profile2" in config and "goal2" in config
    targets2 = None
    if dual:
        config2 = {**config, "profile": config["profile2"], "goal": config["goal2"]}
        targets2 = calculate_targets(config2)
        p1, p2 = config["profile"], config["profile2"]
        print(f"👨 {p1['name']}: TMB {targets['bmr']} | Mant. {targets['tdee']} | Objetivo {targets['target']} cal")
        print(f"👩 {p2['name']}: TMB {targets2['bmr']} | Mant. {targets2['tdee']} | Objetivo {targets2['target']} cal")
    else:
        print(
            f"TMB: {targets['bmr']} cal  |  "
            f"Mantenimiento: {targets['tdee']} cal  |  "
            f"Objetivo: {targets['target']} cal"
        )

    full_plan, wa_msg = generate_meal_plan(config, targets, targets2)

    print()
    print(full_plan)
    print()

    n = config.get("notification", {})
    if n.get("whatsapp_phone") and n.get("whatsapp_apikey"):
        send_whatsapp(config, wa_msg)
    else:
        print("💡 Tip: ejecuta --setup para configurar entrega por WhatsApp.")


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="health_agent",
        description="AI-powered daily meal planner — no API key required.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "examples:\n"
            "  python health_agent.py --setup   # one-time profile setup\n"
            "  python health_agent.py --run     # generate today's meal plan\n"
        ),
    )
    parser.add_argument("--setup", action="store_true", help="Run the interactive setup wizard")
    parser.add_argument("--run",   action="store_true", help="Generate and deliver today's meal plan")
    args = parser.parse_args()

    if args.setup:
        from agent.setup_wizard import run_setup
        run_setup()
    elif args.run:
        run_agent()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
