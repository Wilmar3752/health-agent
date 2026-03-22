# Health Agent

AI-powered daily meal planner. Calculates your personalized calorie target and generates a custom meal plan every morning — powered by Claude Code, zero API key needed.

## Features

- **Personalized calorie math** — BMR (Mifflin-St Jeor) × activity multiplier = TDEE, then adjusts for your goal
- **Goal-aware planning** — lose weight, gain weight, or maintain, with safe daily deficit/surplus caps
- **Per-item calorie counts** — every food item has a portion size and exact calories
- **Macronutrient breakdown** — daily protein / carbs / fat estimate
- **WhatsApp delivery** — free daily message via [CallMeBot](https://www.callmebot.com/blog/free-api-whatsapp-messages/) (no account needed)
- **Terminal output** — full detailed plan printed to stdout
- **Cron-ready** — runs unattended for daily automated delivery
- **No Anthropic API key** — uses your existing Claude Code CLI session

---

## How It Works

```
profile (weight, height, age, activity)
        │
        ▼
   BMR  ──────────────────────────────────────────────────────┐
   (Mifflin-St Jeor)                                          │
        │                                                     │
        ▼                                                     │
   TDEE = BMR × activity multiplier                          │
        │                                                     │
        ▼                                                     │
   Target = TDEE − deficit  (lose weight)                    │
          = TDEE + surplus  (gain weight)                    │
          = TDEE            (maintain)                       │
        │                                                     │
        ▼                                                     │
   Claude Code CLI ──generates──▶ meal plan (full + compact) │
        │                                                     │
        ├──▶ Terminal (full detailed plan)                    │
        └──▶ WhatsApp via CallMeBot (compact summary)         │
                                                              │
   Safety caps ◀────────────────────────────────────────────-┘
     max deficit:  1,000 cal/day (~0.9 kg/week)
     max surplus:    500 cal/day (~0.45 kg/week)
```

---

## Project Structure

```
health-agent/
│
├── health_agent.py          # CLI entry point (--setup / --run)
│
├── agent/                   # Core package
│   ├── __init__.py
│   ├── calculator.py        # BMR, TDEE, goal targets
│   ├── planner.py           # Claude Code meal plan generation
│   ├── notifier.py          # WhatsApp delivery (CallMeBot)
│   └── setup_wizard.py      # Interactive setup wizard
│
├── logs/                    # Run logs (gitignored)
│
├── config.json              # Your profile — created by --setup (gitignored)
├── config.example.json      # Reference config with all fields
├── requirements.txt
├── .env.example
└── .gitignore
```

---

## Installation

**Requirements:** Python 3.11+, [uv](https://docs.astral.sh/uv/), and [Claude Code CLI](https://claude.ai/download) installed and authenticated.

```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone and set up the project
git clone <your-repo>
cd health-agent

# Create virtualenv + install dependencies in one step
uv sync
```

> **No uv?** You can still use plain pip:
> ```bash
> python -m venv .venv && source .venv/bin/activate
> pip install -r requirements.txt
> ```

---

## Quick Start

```bash
# 1. Run the setup wizard (one-time)
uv run python health_agent.py --setup

# 2. Generate today's meal plan
uv run python health_agent.py --run
```

> If your virtualenv is already activated (`source .venv/bin/activate`), you can omit `uv run`.

---

## WhatsApp Setup (optional)

CallMeBot is a free service — no account, no credit card.

1. Save **+34 644 50 10 99** as a contact in WhatsApp
2. Send this exact message to that contact:
   ```
   I allow callmebot to send me messages
   ```
3. You'll receive your personal API key within seconds
4. Enter your phone number and API key when `--setup` asks

Your number must be in international format: `+15551234567`

---

## Automated Daily Delivery

Add a cron job to receive your meal plan every morning at 8 AM:

```bash
crontab -e
```

Add this line (adjust the path):

```
3 8 * * *  cd /path/to/health-agent && uv run python health_agent.py --run >> logs/health_agent.log 2>&1
```

---

## Calorie Math

| Formula | Equation |
|---------|----------|
| BMR (male)   | `10W + 6.25H − 5A + 5`   |
| BMR (female) | `10W + 6.25H − 5A − 161` |
| TDEE | `BMR × activity multiplier` |
| Target (lose) | `TDEE − min(needed_deficit, 1000)` |
| Target (gain) | `TDEE + min(needed_surplus, 500)` |

**Activity multipliers:**

| Level | Multiplier | Description |
|-------|-----------|-------------|
| sedentary | 1.20 | Little or no exercise |
| light | 1.375 | 1-3 days/week |
| moderate | 1.55 | 3-5 days/week |
| active | 1.725 | 6-7 days/week |
| very_active | 1.90 | Physical job or 2× training |

---

## Configuration Reference

See `config.example.json` for all available fields.

```jsonc
{
  "profile": {
    "name": "Your Name",
    "weight_kg": 80,
    "height_cm": 175,
    "age": 30,
    "gender": "male",           // "male" | "female"
    "activity_level": "moderate" // see table above
  },
  "goal": {
    "type": "lose_weight",       // "lose_weight" | "gain_weight" | "maintain"
    "target_weight_kg": 75,
    "timeframe_weeks": 8
  },
  "preferences": {
    "dietary_restrictions": ["vegetarian"],  // optional
    "cuisine": ["Mediterranean"]             // optional
  },
  "notification": {
    "whatsapp_phone":  "+15551234567",  // international format
    "whatsapp_apikey": "123456"         // from CallMeBot
  }
}
```

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Meal plan AI | [Claude Code CLI](https://claude.ai/download) via `claude-agent-sdk` |
| WhatsApp delivery | [CallMeBot](https://www.callmebot.com) free API |
| Calorie formula | Mifflin-St Jeor equation |
| Language | Python 3.10+ |
| Scheduler | System cron |
