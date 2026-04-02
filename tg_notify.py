"""Utilitat per enviar notificacions a Telegram."""
import urllib.request
import urllib.parse

TG_TOKEN   = "8753837839:AAEh0Rjkzih7njLoRF406LhqWb4-VOwFe0s"
TG_CHAT_ID = "4334408"

def notify(msg):
    url  = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    data = urllib.parse.urlencode({"chat_id": TG_CHAT_ID, "text": msg}).encode()
    try:
        urllib.request.urlopen(url, data=data, timeout=10)
    except Exception as e:
        print(f"[tg_notify] Error: {e}")
