# nos.py · utilidades de marca NOSOTROS para láminas 1080x1350
import base64, io, os, urllib.request
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps

W, H = 1080, 1350
ROJO, AMARILLO, TINTA, PAPEL, BLANCO = (225,6,0), (255,212,0), (10,10,12), (243,240,232), (255,255,255)
K = os.path.expanduser("~/nos_kit"); os.makedirs(K, exist_ok=True)

def _font_file(name):
    p = os.path.join(K, name)
    if not os.path.exists(p):
        for d in ("/usr/share/fonts/truetype/google-fonts/",):
            if os.path.exists(d + name): return d + name
        urllib.request.urlretrieve("https://raw.githubusercontent.com/google/fonts/main/ofl/poppins/" + name, p)
    return p

def F(size, peso="xb"):
    """peso: xb=Poppins ExtraBold, b=Poppins Bold, body=cuerpo, bodyb=cuerpo bold"""
    if peso in ("xb", "b"):
        return ImageFont.truetype(_font_file("Poppins-ExtraBold.ttf" if peso == "xb" else "Poppins-Bold.ttf"), size)
    for c in (["Inter-SemiBold.ttf","LiberationSans-Bold.ttf","DejaVuSans-Bold.ttf"] if peso=="bodyb"
              else ["Inter-Regular.ttf","LiberationSans-Regular.ttf","DejaVuSans.ttf"]):
        for root, _, files in os.walk("/usr/share/fonts"):
            if c in files: return ImageFont.truetype(os.path.join(root, c), size)
    return ImageFont.truetype(_font_file("Poppins-Regular.ttf"), size)

def asset(nombre):  # "logo-n" | "marca" | "iconos"
    return Image.open(io.BytesIO(base64.b64decode(B64[nombre]))).convert("RGBA")

def lienzo(color=TINTA):
    return Image.new("RGBA", (W, H), color + (255,))

def foto(path, caja=(0, 0, W, H), foco=(0.5, 0.4)):
    """Recorta la foto para llenar la caja (x0,y0,x1,y1) respetando un punto de foco."""
    im = Image.open(path).convert("RGB")
    w, h = caja[2]-caja[0], caja[3]-caja[1]
    return ImageOps.fit(im, (w, h), Image.LANCZOS, centering=foco).convert("RGBA")

def degradado(img, desde=0.45, hasta=1.0, color=TINTA, opac_max=245, arriba=False):
    """Oscurece de una altura relativa a otra para que el texto se lea."""
    g = Image.new("L", (1, H))
    for y in range(H):
        t = y / H if not arriba else 1 - y / H
        a = 0 if t < desde else min(1, (t - desde) / max(0.01, hasta - desde))
        g.putpixel((0, y), int(opac_max * a))
    capa = Image.new("RGBA", (W, H), color + (0,)); capa.putalpha(g.resize((W, H)))
    return Image.alpha_composite(img, capa)

def sombra(img, capa, xy, radio=18, opac=150, desp=(0, 8)):
    s = Image.new("RGBA", img.size, (0,0,0,0))
    a = capa.split()[-1].point(lambda v: v * opac // 255)
    s.paste((0,0,0,255), (xy[0]+desp[0], xy[1]+desp[1]), a)
    img.alpha_composite(s.filter(ImageFilter.GaussianBlur(radio)))
    img.alpha_composite(capa, xy)

def logo(img, ancho=86, margen=64):
    l = asset("logo-n"); l = l.resize((ancho, int(ancho * l.height / l.width)), Image.LANCZOS)
    sombra(img, l, (W - margen - ancho, margen), radio=10, opac=120, desp=(0, 3))

def tw(d, txt, f):
    b = d.textbbox((0, 0), txt, font=f); return b[2] - b[0]

def envolver(d, txt, f, ancho):
    out, lin = [], ""
    for p in txt.split():
        prueba = (lin + " " + p).strip()
        if tw(d, prueba, f) <= ancho: lin = prueba
        else: out.append(lin); lin = p
    return out + [lin]

def texto_resaltado(img, x, y, txt, clave, f, ancho, color=BLANCO, color_clave=AMARILLO, inter=1.32, centro=False):
    """Escribe un párrafo y pinta en color_clave la frase `clave` (debe aparecer literal en txt). Devuelve y final."""
    d = ImageDraw.Draw(img); i0 = txt.find(clave) if clave else -1
    rango = range(i0, i0 + len(clave)) if i0 >= 0 else range(0)
    lineas, pos = envolver(d, txt, f, ancho), 0
    alto = int(f.size * inter)
    for lin in lineas:
        cx = x + (ancho - tw(d, lin, f)) // 2 if centro else x
        for palabra in lin.split(" "):
            k = txt.find(palabra, pos); pos = k + len(palabra)
            c = color_clave if k in rango else color
            d.text((cx, y), palabra, font=f, fill=c)
            cx += tw(d, palabra + " ", f)
        y += alto
    return y

def caja_texto(img, x, y, txt, f, fondo=ROJO, color=BLANCO, pad=(22, 10), rot=0, sombra_on=True):
    """Titular o etiqueta en caja de color. rot en grados (-3..3 se ve bien). Devuelve (ancho, alto)."""
    d = ImageDraw.Draw(img); b = d.textbbox((0, 0), txt, font=f)
    w, h = b[2] - b[0] + pad[0] * 2, f.size + pad[1] * 2
    c = Image.new("RGBA", (w, h), fondo + (255,))
    ImageDraw.Draw(c).text((pad[0] - b[0], pad[1] - int(f.size * 0.08)), txt, font=f, fill=color)
    if rot: c = c.rotate(rot, expand=True, resample=Image.BICUBIC)
    (sombra if sombra_on else lambda i, cap, xy, **k: i.alpha_composite(cap, xy))(img, c, (x, y))
    return c.size

def cinta(img, y, txt="ÚLTIMA NOTICIA", fondo=ROJO, color=BLANCO, rot=-4, alto=64):
    f = F(int(alto * 0.5), "xb"); d = ImageDraw.Draw(img)
    unidad = f"{txt}  •  "; rep = unidad * (int(W * 1.6 / max(1, tw(d, unidad, f))) + 2)
    c = Image.new("RGBA", (int(W * 1.4), alto), fondo + (255,))
    ImageDraw.Draw(c).text((10, (alto - f.size) // 2 - int(f.size * 0.12)), rep, font=f, fill=color)
    c = c.rotate(rot, expand=True, resample=Image.BICUBIC)
    sombra(img, c, (-(c.width - W) // 2, y), radio=12, opac=120)

def hora_hoy(img, x, y, hhmm):
    """Etiqueta ● HOY + bloque amarillo HH:MM H (hora de México)."""
    f = F(30, "xb"); d = ImageDraw.Draw(img)
    w1 = tw(d, "HOY", f) + 70
    d.rectangle((x, y, x + w1, y + 52), fill=TINTA); d.ellipse((x + 18, y + 19, x + 32, y + 33), fill=ROJO)
    d.text((x + 42, y + 6), "HOY", font=f, fill=BLANCO)
    t = f"{hhmm} H"; w2 = tw(d, t, f) + 36
    d.rectangle((x + w1, y, x + w1 + w2, y + 52), fill=AMARILLO); d.text((x + w1 + 18, y + 6), t, font=f, fill=TINTA)

def sticker(recorte_rgba, borde=14, color=BLANCO):
    """Contorno blanco tipo sticker alrededor de un recorte con transparencia."""
    a = recorte_rgba.split()[-1]; pad = borde * 2
    base = Image.new("L", (a.width + pad * 2, a.height + pad * 2)); base.paste(a, (pad, pad))
    contorno = base.filter(ImageFilter.MaxFilter(borde * 2 + 1)).point(lambda v: 255 if v > 40 else 0)
    out = Image.new("RGBA", base.size, color + (0,)); out.putalpha(contorno)
    out.alpha_composite(recorte_rgba, (pad, pad)); return out

def credito(img, txt, lado="der", color=(255,255,255,170)):
    """Crédito de foto en vertical junto al borde: 'Foto: Autor / CC BY-SA 4.0'."""
    f = F(17, "body"); d = ImageDraw.Draw(img); w = tw(d, txt, f) + 8
    c = Image.new("RGBA", (w, 26), (0,0,0,0)); ImageDraw.Draw(c).text((4, 2), txt, font=f, fill=color)
    c = c.rotate(90, expand=True); x = W - 30 if lado == "der" else 8
    img.alpha_composite(c, (x, max(20, (H - c.height) // 2)))

def puntos(img, i, n, y=H - 70, x=64, activo=ROJO, inactivo=(255,255,255,110)):
    d = ImageDraw.Draw(img); cx = x
    for k in range(n):
        if k == i: d.rounded_rectangle((cx, y, cx + 38, y + 12), 6, fill=activo); cx += 50
        else: d.ellipse((cx, y, cx + 12, y + 12), fill=inactivo); cx += 24

def fuentes_pie(img, txt, y=H - 112, color=(255,255,255,190)):
    ImageDraw.Draw(img).text((64, y), txt, font=F(22, "body"), fill=color)

def cierre(fondo_rgba, acento=(80, 200, 255)):
    """Lámina de cierre: foto lavada, marco de acento, wordmark, Síguenos / para más noticias e íconos."""
    img = fondo_rgba.copy()
    img = Image.alpha_composite(img, Image.new("RGBA", (W, H), (60, 66, 100, 150)))
    d = ImageDraw.Draw(img); m = 52
    d.rectangle((0, 0, W, m), fill=acento); d.rectangle((0, H - m, W, H), fill=acento)
    d.rectangle((0, 0, m, H), fill=acento); d.rectangle((W - m, 0, W, H), fill=acento)
    wm = asset("marca"); wm = wm.resize((340, int(340 * wm.height / wm.width)), Image.LANCZOS)
    img.alpha_composite(wm, ((W - wm.width) // 2, 360))
    f1, f2 = F(132, "b"), F(70, "body"); d = ImageDraw.Draw(img)
    d.text(((W - tw(d, "Síguenos", f1)) // 2, 560), "Síguenos", font=f1, fill=(245, 244, 250))
    t2 = "para más noticias"; w2 = tw(d, t2, f2); x2 = (W - w2) // 2 + 80
    d.rectangle((x2 - 8, 715, x2 + w2 + 8, 800), fill=acento); d.text((x2, 712), t2, font=f2, fill=BLANCO)
    ic = asset("iconos"); ic = ic.resize((700, int(700 * ic.height / ic.width)), Image.LANCZOS)
    img.alpha_composite(ic, ((W - ic.width) // 2, 960))
    return img

def guardar(img, path):
    img.convert("RGB").save(path, "JPEG", quality=92, optimize=True)

B64 = {
    "logo-n": "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",
    "marca": "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",
    "iconos": "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",
}
