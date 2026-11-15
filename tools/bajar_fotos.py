"""Lee pedidos/*.txt (una foto por renglón) y deja en fotos/<pedido>/ los JPG con meta.json.

Cada renglón puede ser:
  - una página de Commons: https://commons.wikimedia.org/wiki/File:Nombre.jpg
  - un título de Commons:  File:Nombre.jpg
  - cualquier URL directa de imagen (sin metadatos de licencia)
Renglones vacíos o que empiezan con # se ignoran.
Al terminar, el pedido se mueve a pedidos/hecho/.
"""
import io, json, os, re, shutil, time, urllib.parse
import requests
from PIL import Image

UA = {"User-Agent": "NOSOTROS-fotos/1.0 (https://github.com/YanWolfgang; noticias)"}
API = "https://commons.wikimedia.org/w/api.php"
MAX = 2160

def limpiar(html):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", html or "")).strip()

def titulo_commons(linea):
    if linea.startswith("File:") or linea.startswith("Archivo:"):
        return "File:" + linea.split(":", 1)[1]
    m = re.search(r"commons\.wikimedia\.org/wiki/((?:File|Archivo):[^?#]+)", linea)
    if m:
        t = urllib.parse.unquote(m.group(1)).replace("_", " ")
        return "File:" + t.split(":", 1)[1]
    return None

def get(url, **kw):
    for intento in range(5):
        r = requests.get(url, headers=UA, timeout=60, **kw)
        if r.status_code == 429:
            time.sleep(5 * (intento + 1)); continue
        r.raise_for_status(); return r
    r.raise_for_status()

def info_commons(titulo):
    r = get(API, params={"action": "query", "format": "json", "titles": titulo, "prop": "imageinfo",
                         "iiprop": "url|extmetadata|size", "iiurlwidth": MAX})
    p = next(iter(r.json()["query"]["pages"].values()))
    if "imageinfo" not in p:
        raise ValueError(f"No existe en Commons: {titulo}")
    ii = p["imageinfo"][0]; md = ii.get("extmetadata", {})
    v = lambda k: limpiar(md.get(k, {}).get("value", ""))
    return {
        "url": ii.get("thumburl") or ii["url"],
        "pagina": ii.get("descriptionurl", ""),
        "autor": v("Artist") or v("Credit"),
        "licencia": v("LicenseShortName"),
        "licencia_url": v("LicenseUrl"),
        "descripcion": v("ImageDescription")[:300],
    }

def procesar(linea, destino, n):
    t = titulo_commons(linea)
    meta = info_commons(t) if t else {"url": linea, "pagina": linea, "autor": "", "licencia": "", "licencia_url": "", "descripcion": ""}
    meta["origen"] = linea
    im = Image.open(io.BytesIO(get(meta["url"]).content))
    im = im.convert("RGB"); im.thumbnail((MAX, MAX))
    nombre = f"{n:02d}.jpg"; im.save(os.path.join(destino, nombre), "JPEG", quality=92)
    meta.update({"archivo": nombre, "ancho": im.width, "alto": im.height})
    meta["credito"] = f"Foto: {meta['autor'] or 'Autor desconocido'} / {meta['licencia'] or 'licencia por confirmar'}"
    return meta

def main():
    os.makedirs("pedidos/hecho", exist_ok=True)
    for f in sorted(os.listdir("pedidos")):
        if not f.endswith(".txt"): continue
        pid = f[:-4]; destino = os.path.join("fotos", pid); os.makedirs(destino, exist_ok=True)
        lineas = [l.strip() for l in open(os.path.join("pedidos", f), encoding="utf-8")]
        lineas = [l for l in lineas if l and not l.startswith("#")]
        resultado = []
        for n, l in enumerate(lineas, 1):
            try:
                resultado.append(procesar(l, destino, n))
            except Exception as e:
                resultado.append({"origen": l, "error": str(e)})
            time.sleep(2)
        json.dump(resultado, open(os.path.join(destino, "meta.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        shutil.move(os.path.join("pedidos", f), os.path.join("pedidos", "hecho", f))
        print(pid, sum(1 for r in resultado if "error" not in r), "de", len(resultado))

if __name__ == "__main__":
    main()
