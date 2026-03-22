"""
WhatsApp delivery via CallMeBot (https://www.callmebot.com).

Free tier — no account or credit card required.
One-time activation per phone number (see README for instructions).
"""

import urllib.error
import urllib.parse
import urllib.request


CALLMEBOT_URL = "https://api.callmebot.com/whatsapp.php"
REQUEST_TIMEOUT = 15  # seconds


def send_whatsapp(config: dict, message: str) -> bool:
    """
    Send a WhatsApp message via CallMeBot.

    Reads whatsapp_phone and whatsapp_apikey from config["notification"].
    Returns True if the message was queued successfully.
    """
    n      = config.get("notification", {})
    phone  = n.get("whatsapp_phone", "").strip()
    apikey = n.get("whatsapp_apikey", "").strip()

    if not phone or not apikey:
        return False

    params = urllib.parse.urlencode({
        "phone":  phone,
        "text":   message,
        "apikey": apikey,
    })
    url = f"{CALLMEBOT_URL}?{params}"

    try:
        with urllib.request.urlopen(url, timeout=REQUEST_TIMEOUT) as resp:
            body = resp.read().decode("utf-8", errors="ignore")
            if resp.status == 200 and "Message queued" in body:
                print(f"✅ Plan enviado por WhatsApp a {phone}")
                return True
            print(f"⚠️  CallMeBot respondió ({resp.status}): {body[:140]}")
            return False

    except urllib.error.HTTPError as e:
        print(f"❌ Error HTTP al enviar WhatsApp ({e.code}): {e.reason}")
        return False
    except Exception as e:
        print(f"❌ No se pudo enviar el WhatsApp: {e}")
        return False
