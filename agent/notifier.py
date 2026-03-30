"""
WhatsApp delivery via Kapso CLI (https://docs.kapso.ai).
Uses `kapso whatsapp messages send` to avoid Cloudflare restrictions on direct API calls.
"""

import subprocess


def _send_to(name: str, phone: str, phone_number_id: str, message: str) -> bool:
    result = subprocess.run(
        [
            "kapso", "whatsapp", "messages", "send",
            "--phone-number-id", phone_number_id,
            "--to", phone,
            "--text", message,
            "--output", "human",
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        print(f"✅ Plan enviado por WhatsApp a {name} ({phone})")
        return True
    error = (result.stderr or result.stdout).strip()[:200]
    print(f"❌ Error al enviar a {name} ({phone}): {error}")
    return False


def send_whatsapp(config: dict, message: str) -> None:
    """Send the meal plan to all configured WhatsApp numbers via Kapso CLI."""
    n = config.get("notification", {})
    phone_number_id = n.get("kapso_phone_number_id", "").strip()

    if not phone_number_id:
        print("⚠️  Falta kapso_phone_number_id en notification.")
        return

    phones = []
    if p := config.get("profile", {}).get("whatsapp_phone", "").strip():
        phones.append((config["profile"]["name"], p))
    if p := config.get("profile2", {}).get("whatsapp_phone", "").strip():
        phones.append((config["profile2"]["name"], p))

    if not phones:
        print("⚠️  No hay números de WhatsApp configurados en los perfiles.")
        return

    for name, phone in phones:
        _send_to(name, phone, phone_number_id, message)
