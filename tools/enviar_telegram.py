"""Manda a Telegram cada carpeta envios/<id>/ que no tenga ENVIADO.txt.

Dentro de la carpeta:
  01.jpg, 02.jpg ...   láminas en orden (álbum, máximo 10)
  mensaje.txt          texto que va después del álbum (copy, copy corto, fuentes)
Al terminar escribe ENVIADO.txt (o ERROR.txt) en la carpeta.
"""
import os, sys, json, requests

TOKEN, CHAT = os.environ.get("TELEGRAM_BOT_TOKEN"), os.environ.get("TELEGRAM_CHAT_ID")
API = f"https://api.telegram.org/bot{TOKEN}"

def partes(texto, n=4000):
    out = []
    while texto:
        corte = texto.rfind("\n", 0, n) if len(texto) > n else len(texto)
        corte = corte if corte > 0 else n
        out.append(texto[:corte]); texto = texto[corte:].lstrip("\n")
    return out

def enviar(carpeta):
    imgs = sorted(f for f in os.listdir(carpeta) if f.lower().endswith((".jpg", ".jpeg", ".png")))[:10]
    if len(imgs) >= 2:
        files = {f"f{i}": open(os.path.join(carpeta, f), "rb") for i, f in enumerate(imgs)}
        media = [{"type": "photo", "media": f"attach://f{i}"} for i in range(len(imgs))]
        r = requests.post(f"{API}/sendMediaGroup", data={"chat_id": CHAT, "media": json.dumps(media)}, files=files, timeout=120)
        r.raise_for_status()
    elif imgs:
        r = requests.post(f"{API}/sendPhoto", data={"chat_id": CHAT}, files={"photo": open(os.path.join(carpeta, imgs[0]), "rb")}, timeout=120)
        r.raise_for_status()
    msg = os.path.join(carpeta, "mensaje.txt")
    if os.path.exists(msg):
        for p in partes(open(msg, encoding="utf-8").read().strip()):
            requests.post(f"{API}/sendMessage", data={"chat_id": CHAT, "text": p, "disable_web_page_preview": "true"}, timeout=60).raise_for_status()

def descubrir_chat():
    """Sin TELEGRAM_CHAT_ID: lee los últimos mensajes que recibió el bot y anota los chats en envios/CHATS.txt."""
    r = requests.get(f"{API}/getUpdates", timeout=60); r.raise_for_status()
    chats = {}
    for u in r.json().get("result", []):
        m = u.get("message") or u.get("channel_post") or u.get("my_chat_member") or {}
        c = m.get("chat") or {}
        if c: chats[c["id"]] = c.get("title") or " ".join(x for x in (c.get("first_name"), c.get("last_name")) if x) or c.get("username", "")
    txt = "\n".join(f"{k}  {v}" for k, v in chats.items()) or "Sin mensajes. Mándale cualquier mensaje al bot y vuelve a correr."
    open("envios/CHATS.txt", "w", encoding="utf-8").write(txt + "\n"); print(txt)

def main():
    if TOKEN and not CHAT:
        descubrir_chat(); return
    if not TOKEN or not CHAT:
        print("Faltan los secrets TELEGRAM_BOT_TOKEN y TELEGRAM_CHAT_ID"); sys.exit(1)
    for d in sorted(os.listdir("envios")):
        c = os.path.join("envios", d)
        if not os.path.isdir(c) or os.path.exists(os.path.join(c, "ENVIADO.txt")): continue
        try:
            enviar(c); open(os.path.join(c, "ENVIADO.txt"), "w").write("ok\n"); print("enviado", d)
        except Exception as e:
            open(os.path.join(c, "ERROR.txt"), "w").write(str(e)[:500]); print("error", d, e)

if __name__ == "__main__":
    main()
