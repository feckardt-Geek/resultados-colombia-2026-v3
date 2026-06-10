#!/usr/bin/env python3
"""
Dashboard local — Elecciones Presidenciales Colombia 2026 (Primera vuelta).

Servidor sin dependencias externas (solo librería estándar de Python).
Expone:
  - /                -> dashboard (web/index.html)
  - /api/resultados  -> JSON normalizado con boletín, mesas y candidatos

FUENTE DE DATOS
---------------
Consume el feed JSON OFICIAL de la Registraduría Nacional (el mismo que alimenta
resultados.registraduria.gov.co), descubierto desde el bundle del portal:

    Resultados nacionales:  /json/ACT/PR/00.json   (PR = Presidente, 00 = Colombia)
    Nomenclátor partidos:   /json/nomenclator.json (códigos -> nombre y color)

Si el feed oficial no está disponible, cae a una SIMULACIÓN claramente
etiquetada para que el dashboard siga siendo usable.

Uso:
    python3 server.py                  # http://localhost:8000  (datos OFICIALES)
    PORT=9000 python3 server.py
    REGISTRADURIA_JSON_URL=https://... python3 server.py   # forzar otro feed
"""

import json
import os
import ssl
import sys
import time
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs

BASE_DIR = Path(__file__).resolve().parent
WEB_DIR = BASE_DIR / "web"


def _cargar_dotenv():
    """Carga BASE_DIR/.env (clave=valor) sin pisar variables ya definidas."""
    env = BASE_DIR / ".env"
    if not env.exists():
        return
    try:
        for linea in env.read_text("utf-8").splitlines():
            linea = linea.strip()
            if not linea or linea.startswith("#") or "=" not in linea:
                continue
            k, v = linea.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
    except Exception:
        pass


_cargar_dotenv()

PORT = int(os.environ.get("PORT", "8000"))

# --- Asistente IA (Google Gemini) -------------------------------------------
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-flash-latest").strip()
GEMINI_URL = ("https://generativelanguage.googleapis.com/v1beta/models/"
              f"{GEMINI_MODEL}:generateContent")
IA_SISTEMA = (
    "Eres un asistente experto que ayuda a entender el tablero de resultados de "
    "las elecciones presidenciales de Colombia 2026. Responde SIEMPRE en español, "
    "de forma breve, clara y neutral. Básate ÚNICAMENTE en los datos del CONTEXTO "
    "que se te entrega (son datos reales del tablero). Si la respuesta no está en "
    "el contexto, dilo con honestidad y no inventes cifras. No des recomendaciones "
    "de voto ni opiniones partidistas; limítate a explicar los datos."
)

# --- Endpoints oficiales de la Registraduría (descubiertos del portal) --------
PORTAL = "https://resultados.registraduria.gov.co"
OFICIAL_URL = os.environ.get(
    "REGISTRADURIA_JSON_URL", f"{PORTAL}/json/ACT/PR/00.json"
).strip()
NOMENCLATOR_URL = f"{PORTAL}/json/nomenclator.json"
FUENTE_PORTAL = f"{PORTAL}/"

# CloudFront exige cabeceras de navegador (Referer/Origin) en los feeds de datos.
HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) "
                   "Chrome/124.0 Safari/537.36"),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "es-CO,es;q=0.9,en;q=0.8",
    "Referer": FUENTE_PORTAL,
    "Origin": PORTAL,
    # Fuerzan a CloudFront a revalidar y devolver el ULTIMO boletin
    # (si no, sirve una version cacheada con un boletin viejo).
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
}

MESAS_TOTAL_DEF = 122000
CENSO_DEF = 41_000_000
_INICIO = time.time()           # ancla de la simulación de respaldo
_NOMEN_CACHE = {"ts": 0, "data": None}   # caché del nomenclátor (colores/partidos)


# ---------------------------------------------------------------------------
# Utilidades de parseo (el feed usa formato español: "47,32%", enteros string)
# ---------------------------------------------------------------------------
def _num(s, default=0.0):
    """'47,32%' -> 47.32 ; '24965' -> 24965.0 ; '' -> default."""
    if s is None:
        return default
    t = str(s).replace("%", "").replace(".", "").replace(",", ".").strip()
    try:
        return float(t)
    except ValueError:
        return default


def _int(s, default=0):
    return int(_num(s, default))


def _titulo(s):
    """'IVÁN CEPEDA CASTRO' -> 'Iván Cepeda Castro' (respetando minúsculas de enlace)."""
    if not s:
        return ""
    menores = {"de", "la", "las", "los", "del", "y", "e"}
    palabras = s.strip().split()
    out = []
    for i, w in enumerate(palabras):
        wl = w.lower()
        out.append(wl if (wl in menores and i > 0) else wl.capitalize())
    return " ".join(out)


def _build_ssl_context():
    """Contexto SSL con verificación ACTIVA usando un bundle de CAs real.

    Carga el almacén del SISTEMA operativo y, además, el de certifi. Así cubre:
      · CAs públicas estándar (vía certifi o el sistema),
      · raíces corporativas / de antivirus que interceptan TLS en Windows
        (sólo están en el almacén de Windows, no en certifi),
      · macOS, donde Python no usa el llavero del sistema por defecto (certifi
        lo cubre).
    Mantiene siempre la verificación activada.
    """
    ctx = ssl.create_default_context()      # carga el almacén del SO (Windows/Linux)
    try:
        import certifi
        ctx.load_verify_locations(cafile=certifi.where())   # + CAs públicas
    except Exception:
        pass
    for ruta in ("/etc/ssl/cert.pem",                       # macOS / BSD
                 "/etc/ssl/certs/ca-certificates.crt",       # Debian/Ubuntu
                 "/etc/pki/tls/certs/ca-bundle.crt"):        # RHEL/Fedora
        if os.path.exists(ruta):
            try:
                ctx.load_verify_locations(cafile=ruta)
            except Exception:
                continue
    return ctx


_SSL = _build_ssl_context()


def _fetch_json(url, timeout=10, bust=False):
    # bust=True añade un parámetro único para saltar la caché de CloudFront
    # (si no, devuelve un boletín viejo cacheado en vez del último).
    if bust:
        sep = "&" if "?" in url else "?"
        url = f"{url}{sep}_={int(time.time() * 1000)}"
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=timeout, context=_SSL) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _nomen_raw():
    """Nomenclátor crudo (cacheado 1h): partidos + lista de departamentos."""
    ahora = time.time()
    if _NOMEN_CACHE.get("raw") and ahora - _NOMEN_CACHE["ts"] < 3600:
        return _NOMEN_CACHE["raw"]
    try:
        raw = _fetch_json(NOMENCLATOR_URL, timeout=12)
        partidos = {}
        for p in raw.get("partidos", []):
            # El 'codpar' de cada candidato coincide con el campo 'i' del partido.
            partidos[_int(p.get("i"))] = {
                "nombre": _titulo(p.get("nombre", "")),
                "color": p.get("color") or "#7F8C8D",
            }
        deptos = []
        amb = raw.get("amb") or []
        for a in (amb[0].get("ambitos", []) if amb else []):
            if a.get("l") == 2:                       # nivel 2 = departamento
                deptos.append((_titulo(a.get("n", "")), a.get("co", "")))
        deptos.sort(key=lambda x: x[0])
        _NOMEN_CACHE.update(ts=ahora, raw=raw, partidos=partidos, deptos=deptos)
    except Exception:
        pass
    return _NOMEN_CACHE.get("raw")


def _nomenclator():
    """Mapa { codpar(int) -> {'nombre','color'} } de partidos."""
    _nomen_raw()
    return _NOMEN_CACHE.get("partidos") or {}


def _lista_departamentos():
    """[(nombre, código)] de los 34 departamentos, orden alfabético."""
    _nomen_raw()
    return _NOMEN_CACHE.get("deptos") or []


def _fmt_mdhm(mdhm):
    """'05311623' (MMDDHHMM) -> '31/05/2026 16:23'."""
    s = str(mdhm or "")
    if len(s) == 8 and s.isdigit():
        mm, dd, hh, mi = s[0:2], s[2:4], s[4:6], s[6:8]
        return f"{dd}/{mm}/2026 {hh}:{mi}"
    return time.strftime("%d/%m/%Y %H:%M")


# Códigos de candidatos clave (act.codpar == campo 'i' del nomenclátor).
COD_CEPEDA, COD_ABELARDO, COD_PALOMA = 7, 10, 2


def _ambito_resumen(nombre, codigo, partidos):
    """Resumen de un ámbito (depto/ciudad): 1.º y 2.º lugar con nombre, votos y %."""
    try:
        raw = _fetch_json(f"{PORTAL}/json/ACT/PR/{codigo}.json", timeout=8, bust=True)
    except Exception:
        return None
    tot = (raw.get("totales") or {}).get("act") or {}
    cam = raw.get("camaras") or []
    pt = (cam[0].get("partotabla") if cam else []) or []
    items = []
    for p in pt:
        a = p.get("act") or {}
        cans = a.get("cantotabla") or []
        can = cans[0] if isinstance(cans, list) and cans else (cans if isinstance(cans, dict) else {})
        meta = partidos.get(_int(a.get("codpar")), {})
        items.append({
            "nombre": _titulo(f"{can.get('nomcan','')} {can.get('apecan','')}"),
            "codpar": _int(a.get("codpar")),
            "color": meta.get("color", "#7F8C8D"),
            "votos": _int(a.get("vot")),
            "pct": round(_num(a.get("pvot")), 2),
        })
    items.sort(key=lambda x: x["votos"], reverse=True)
    vacio = {"nombre": "—", "codpar": 0, "color": "#CFC9BA", "votos": 0, "pct": 0.0}
    primero = items[0] if items else dict(vacio)
    segundo = items[1] if len(items) > 1 else dict(vacio)
    pal = next((it for it in items if it["codpar"] == COD_PALOMA), None)
    pal = pal or {"nombre": "Paloma Valencia Laserna", "codpar": COD_PALOMA,
                  "color": "#4BAFE7", "votos": 0, "pct": 0.0}
    return {
        "nombre": nombre, "codigo": codigo,
        "primero": primero, "segundo": segundo, "paloma": pal,
        "lider": primero["nombre"], "lider_codpar": primero["codpar"],
        "color": primero["color"],
        "participacion_pct": round(_num(tot.get("pvotant")), 2),
        "mesas_pct": round(_num(tot.get("pmesesc")), 2),
        "votantes": _int(tot.get("votant")),
        "censo": _int(tot.get("centota")),
        "abstencion_pct": round(_num(tot.get("pabsten")), 2),
    }


def _fetch_ambitos(items):
    """Descarga ámbitos en paralelo; conserva el orden de `items`."""
    partidos = _nomenclator()
    res = [None] * len(items)
    with ThreadPoolExecutor(max_workers=12) as ex:
        futs = {ex.submit(_ambito_resumen, n, c, partidos): i
                for i, (n, c) in enumerate(items)}
        for f in futs:
            try:
                res[futs[f]] = f.result()
            except Exception:
                pass
    return [r for r in res if r]


def _conteo_lideres(ambitos):
    """Cuántos ámbitos ganó cada candidato (para la tabla resumen)."""
    agg = {}
    for a in ambitos:
        k = a["lider"]
        if k not in agg:
            agg[k] = {"nombre": k, "color": a["color"], "ganados": 0}
        agg[k]["ganados"] += 1
    return sorted(agg.values(), key=lambda x: x["ganados"], reverse=True)


# Top 20 ciudades por población (DANE) -> código de ámbito de la Registraduría.
CIUDADES = [
    ("Bogotá", "16001"), ("Medellín", "01001"), ("Cali", "31001"),
    ("Barranquilla", "03001"), ("Cartagena", "05001"), ("Cúcuta", "25001"),
    ("Soledad", "03052"), ("Ibagué", "29001"), ("Bucaramanga", "27001"),
    ("Soacha", "15247"), ("Santa Marta", "21001"), ("Villavicencio", "52001"),
    ("Bello", "01049"), ("Valledupar", "12001"), ("Pereira", "24001"),
    ("Montería", "13001"), ("Pasto", "23001"), ("Manizales", "09001"),
    ("Neiva", "19001"), ("Palmira", "31079"),
]
_CIUDADES_CACHE = {"ts": 0, "data": None}
_DEPTOS_CACHE = {"ts": 0, "data": None}


def obtener_ciudades():
    """Top 20 ciudades (orden poblacional). Fetch concurrente + caché de 25 s."""
    ahora = time.time()
    if _CIUDADES_CACHE["data"] and ahora - _CIUDADES_CACHE["ts"] < 25:
        return _CIUDADES_CACHE["data"]
    data = _fetch_ambitos(CIUDADES)
    payload = {
        "ciudades": data,                      # conserva el orden poblacional
        "orden": "Ordenadas por población (DANE)",
        "fuente": "OFICIAL" if data else "SIN DATOS",
    }
    _CIUDADES_CACHE.update(ts=ahora, data=payload)
    return payload


def obtener_departamentos():
    """34 departamentos con líder y votación clave + conteo de ganados. Caché 25 s."""
    ahora = time.time()
    if _DEPTOS_CACHE["data"] and ahora - _DEPTOS_CACHE["ts"] < 25:
        return _DEPTOS_CACHE["data"]
    data = sorted(_fetch_ambitos(_lista_departamentos()), key=lambda x: x["nombre"])
    payload = {
        "departamentos": data,
        "conteo": _conteo_lideres(data),
        "fuente": "OFICIAL" if data else "SIN DATOS",
    }
    _DEPTOS_CACHE.update(ts=ahora, data=payload)
    return payload


# ---------------------------------------------------------------------------
# Drill-down: municipios de un departamento con los 3 candidatos principales
# ---------------------------------------------------------------------------
_MUNI_CACHE = {}  # codigo_depto -> {"ts","data"}


def _muni_resumen(nombre, codigo, partidos):
    try:
        raw = _fetch_json(f"{PORTAL}/json/ACT/PR/{codigo}.json", timeout=8, bust=True)
    except Exception:
        return None
    tot = (raw.get("totales") or {}).get("act") or {}
    cam = raw.get("camaras") or []
    pt = (cam[0].get("partotabla") if cam else []) or []
    por, mejor = {}, (-1, 0)
    for p in pt:
        a = p.get("act") or {}
        cp = _int(a.get("codpar"))
        cans = a.get("cantotabla") or []
        can = cans[0] if isinstance(cans, list) and cans else (cans if isinstance(cans, dict) else {})
        v = _int(a.get("vot"))
        por[cp] = {"nombre": _titulo(f"{can.get('nomcan','')} {can.get('apecan','')}"),
                   "votos": v, "pct": round(_num(a.get("pvot")), 2)}
        if v > mejor[0]:
            mejor = (v, cp)

    def g(cp, fb):
        d = por.get(cp) or {}
        return {"nombre": d.get("nombre", fb), "votos": d.get("votos", 0), "pct": d.get("pct", 0.0)}

    return {
        "nombre": nombre, "codigo": codigo,
        "abelardo": g(COD_ABELARDO, "Abelardo de la Espriella"),
        "cepeda": g(COD_CEPEDA, "Iván Cepeda Castro"),
        "paloma": g(COD_PALOMA, "Paloma Valencia Laserna"),
        "votantes": _int(tot.get("votant")),
        "mesas_pct": round(_num(tot.get("pmesesc")), 2),
        "ganador": mejor[1],
    }


def obtener_municipios(deptcode):
    """Municipios de un departamento, cada uno con De la Espriella, Cepeda y
    Valencia (votos + %). Concurrente + caché 5 min por departamento."""
    ahora = time.time()
    c = _MUNI_CACHE.get(deptcode)
    if c and ahora - c["ts"] < 300:
        return c["data"]
    partidos = _nomenclator()
    try:
        raw = _fetch_json(f"{PORTAL}/json/ACT/PR/{deptcode}.json", timeout=10, bust=True)
    except Exception as e:
        return {"ok": False, "municipios": [], "error": str(e)}
    mg = (raw.get("camaras") or [{}])[0].get("mapagan") or []
    items = [(_titulo(m.get("nombre", "")), m.get("amb", "")) for m in mg if m.get("amb")]
    res = [None] * len(items)
    with ThreadPoolExecutor(max_workers=12) as ex:
        futs = {ex.submit(_muni_resumen, n, cod, partidos): i for i, (n, cod) in enumerate(items)}
        for f in futs:
            try:
                res[futs[f]] = f.result()
            except Exception:
                pass
    munis = [r for r in res if r]
    munis.sort(key=lambda x: x["votantes"], reverse=True)
    payload = {"ok": True, "departamento": deptcode, "total": len(munis), "municipios": munis}
    _MUNI_CACHE[deptcode] = {"ts": ahora, "data": payload}
    return payload


# ---------------------------------------------------------------------------
# Colombianos en el exterior (ámbito "Consulados" = código 88), por país
# ---------------------------------------------------------------------------
_EXT_CACHE = {"ts": 0, "data": None}


def obtener_exterior():
    """Voto en el exterior: totales, candidatos y desglose por país. Caché 25 s."""
    ahora = time.time()
    if _EXT_CACHE["data"] and ahora - _EXT_CACHE["ts"] < 25:
        return _EXT_CACHE["data"]
    partidos = _nomenclator()
    try:
        raw = _fetch_json(f"{PORTAL}/json/ACT/PR/88.json", timeout=10, bust=True)
    except Exception as e:
        return {"ok": False, "error": str(e), "candidatos": [], "paises": []}
    tot = (raw.get("totales") or {}).get("act") or {}
    cam = raw.get("camaras") or []
    pt = (cam[0].get("partotabla") if cam else []) or []
    cands = []
    for p in pt:
        a = p.get("act") or {}
        cans = a.get("cantotabla") or []
        can = cans[0] if isinstance(cans, list) and cans else (cans if isinstance(cans, dict) else {})
        meta = partidos.get(_int(a.get("codpar")), {})
        cands.append({
            "nombre": _titulo(f"{can.get('nomcan','')} {can.get('apecan','')}"),
            "color": meta.get("color", "#7F8C8D"),
            "votos": _int(a.get("vot")), "pct": round(_num(a.get("pvot")), 2),
        })
    cands.sort(key=lambda x: x["votos"], reverse=True)
    paises = []
    for d in (cam[0].get("mapagan") if cam else []) or []:
        can = d.get("cantotabla") or {}
        if isinstance(can, list):
            can = can[0] if can else {}
        meta = partidos.get(_int(d.get("codpar")), {})
        paises.append({
            "nombre": _titulo(d.get("nombre", "")),
            "lider": _titulo(f"{can.get('nomcan','')} {can.get('apecan','')}"),
            "color": meta.get("color", "#7F8C8D"),
            "lider_pct": round(_num(d.get("pvot")), 2),
            "votantes": _int(d.get("votant")),
            "mesas_pct": round(_num(d.get("pmesesc")), 2),
        })
    paises.sort(key=lambda x: x["votantes"], reverse=True)
    payload = {
        "ok": True,
        "votantes": _int(tot.get("votant")),
        "mesas_informadas": _int(tot.get("mesesc")),
        "mesas_total": _int(tot.get("metota")),
        "mesas_pct": round(_num(tot.get("pmesesc")), 2),
        "candidatos": cands[:6],
        "paises": paises,
    }
    _EXT_CACHE.update(ts=ahora, data=payload)
    return payload


# ---------------------------------------------------------------------------
# Polymarket: probabilidades de mercado para 1.ª y 2.ª vuelta
# ---------------------------------------------------------------------------
POLY_BASE = "https://gamma-api.polymarket.com/events?slug="
_POLY_HEADERS = {"User-Agent": HEADERS["User-Agent"], "Accept": "application/json"}
_POLY_CACHE = {"ts": 0, "data": None}


def _poly_event(slug):
    req = urllib.request.Request(POLY_BASE + slug, headers=_POLY_HEADERS)
    with urllib.request.urlopen(req, timeout=10, context=_SSL) as r:
        arr = json.loads(r.read().decode("utf-8"))
    return arr[0] if isinstance(arr, list) and arr else {}


def _poly_outcomes(ev, limite=5):
    """Extrae [{nombre, prob}] de un evento, ordenado por probabilidad."""
    out = []
    for m in ev.get("markets", []):
        gi = (m.get("groupItemTitle") or m.get("question") or "").strip()
        if not gi or gi.startswith("Candidate "):      # descarta placeholders
            continue
        prob = None
        try:
            outs = json.loads(m.get("outcomes", "[]"))
            prices = json.loads(m.get("outcomePrices", "[]"))
            for o, pr in zip(outs, prices):
                if str(o).lower() == "yes":
                    prob = float(pr)
            if prob is None and prices:
                prob = float(prices[0])
        except Exception:
            pass
        if prob is None and m.get("lastTradePrice") is not None:
            prob = float(m.get("lastTradePrice"))
        if prob is None or prob < 0.005:
            continue
        out.append({"nombre": gi, "prob": round(prob, 3)})
    out.sort(key=lambda x: x["prob"], reverse=True)
    return out[:limite]


def obtener_polymarket():
    """Probabilidades de Polymarket (caché 60 s)."""
    ahora = time.time()
    if _POLY_CACHE["data"] and ahora - _POLY_CACHE["ts"] < 60:
        return _POLY_CACHE["data"]
    try:
        pres = _poly_event("colombia-presidential-election")
        r1 = _poly_event("colombia-presidential-election-1st-round-winner")
        adv = _poly_event("colombia-election-who-will-advance-to-2nd-round")
        payload = {
            "ok": True,
            "fuente": "Polymarket",
            "url": "https://polymarket.com/event/colombia-presidential-election",
            "cierre_presidencia": pres.get("endDate", ""),
            "presidencia": _poly_outcomes(pres, 4),       # ganador 2.ª vuelta
            "primera_ganador": _poly_outcomes(r1, 4),      # ganador 1.ª vuelta
            "pasa_segunda": _poly_outcomes(adv, 4),        # dupla que pasa
        }
    except Exception as e:
        payload = {"ok": False, "error": str(e),
                   "presidencia": [], "primera_ganador": [], "pasa_segunda": []}
    _POLY_CACHE.update(ts=ahora, data=payload)
    return payload


# ---------------------------------------------------------------------------
# Normalización del feed OFICIAL al esquema del dashboard
# ---------------------------------------------------------------------------
def _normalizar_oficial(raw):
    partidos = _nomenclator()
    tot = (raw.get("totales") or {}).get("act") or {}

    metota = _int(tot.get("metota"), MESAS_TOTAL_DEF)
    mesesc = _int(tot.get("mesesc"))
    pmesesc = _num(tot.get("pmesesc"))
    if not pmesesc and metota:
        pmesesc = round(mesesc / metota * 100, 2)

    candidatos = []
    por_cod = {}
    camaras = raw.get("camaras") or []
    partotabla = (camaras[0].get("partotabla") if camaras else []) or []
    for p in partotabla:
        act = p.get("act") or {}
        cans = act.get("cantotabla") or []
        can = cans[0] if cans else {}
        nombre = _titulo(f"{can.get('nomcan','')} {can.get('apecan','')}")
        codpar = _int(act.get("codpar"))
        meta = partidos.get(codpar, {})
        votos = _int(act.get("vot"))
        pcent = round(_num(act.get("pvot")), 2)
        por_cod[codpar] = {"votos": votos, "pct": pcent}
        candidatos.append({
            "nombre": nombre or "—",
            "partido": meta.get("nombre", "—"),
            "color": meta.get("color", "#7F8C8D"),
            "votos": votos,
            "porcentaje": pcent,
        })

    # Comparativo: Cepeda vs. suma del bloque de derecha (De la Espriella + Valencia)
    ce = por_cod.get(COD_CEPEDA, {"votos": 0, "pct": 0.0})
    ab = por_cod.get(COD_ABELARDO, {"votos": 0, "pct": 0.0})
    pa = por_cod.get(COD_PALOMA, {"votos": 0, "pct": 0.0})
    comparativo = {
        "cepeda": ce, "abelardo": ab, "paloma": pa,
        "suma": {"votos": ab["votos"] + pa["votos"], "pct": round(ab["pct"] + pa["pct"], 2)},
    }

    # Voto en blanco (de los totales) como fila final, en gris neutro.
    votblan = _int(tot.get("votblan"))
    if votblan:
        candidatos.append({
            "nombre": "Voto en blanco",
            "partido": "—",
            "color": "#9AA0A6",
            "votos": votblan,
            "porcentaje": round(_num(tot.get("pvotblan")), 2),
        })

    candidatos.sort(key=lambda x: x["votos"], reverse=True)

    return {
        "eleccion": "Presidencia de la República 2026 — Primera vuelta",
        "fecha_jornada": "2026-05-31",
        "boletin": _int(raw.get("numact")),
        "fecha_corte_txt": _fmt_mdhm(raw.get("mdhm")),
        "mesas_informadas": mesesc,
        "mesas_total": metota,
        "porcentaje_mesas": round(pmesesc, 2),
        "votos_totales": _int(tot.get("votant")),
        "participacion_pct": round(_num(tot.get("pvotant")), 2),
        "abstencion": _int(tot.get("absten")),
        "abstencion_pct": round(_num(tot.get("pabsten")), 2),
        "censo": _int(tot.get("centota"), CENSO_DEF),
        "desglose": {
            "validos": _int(tot.get("votval")), "validos_pct": round(_num(tot.get("pvotval")), 2),
            "blanco": _int(tot.get("votblan")), "blanco_pct": round(_num(tot.get("pvotblan")), 2),
            "nulos": _int(tot.get("votnul")), "nulos_pct": round(_num(tot.get("pvotnul")), 2),
            "no_marcados": _int(tot.get("votnma")), "no_marcados_pct": round(_num(tot.get("pvotnma")), 2),
        },
        "comparativo": comparativo,
        "fuente": "OFICIAL",
        "fuente_nota": ("Resultados preliminares oficiales de la Registraduría Nacional "
                        "del Estado Civil (sin valor jurídico hasta el escrutinio). "
                        f"Actualización N.° {_int(raw.get('numact'))} · "
                        f"corte {_fmt_mdhm(raw.get('mdhm'))}."),
        "fuente_url": OFICIAL_URL,
        "candidatos": candidatos,
    }


# ---------------------------------------------------------------------------
# Simulación de respaldo (lista real de candidatos; votos ilustrativos)
# ---------------------------------------------------------------------------
_SIM = [
    ("Iván Cepeda Castro", "Movimiento Político Pacto Histórico", "#8C378C", 31.5),
    ("Abelardo de la Espriella", "Defensores de la Patria", "#CE742A", 24.0),
    ("Paloma Valencia Laserna", "Partido Centro Democrático", "#4BAFE7", 18.5),
    ("Sergio Fajardo Valderrama", "Dignidad & Compromiso", "#F1AC22", 9.5),
    ("Claudia López", "Con Claudia Imparables", "#D0D022", 7.0),
    ("Otros candidatos", "Varias colectividades", "#7F8C8D", 6.5),
    ("Voto en blanco", "—", "#9AA0A6", 3.0),
]


def _simular_avance(nota_extra=""):
    transcurrido = time.time() - _INICIO
    pct = round(min(99.9, transcurrido / 8.0), 2)
    mesas = int(MESAS_TOTAL_DEF * pct / 100.0)
    votos = int(CENSO_DEF * 0.52 * pct / 100.0)
    cands = [{
        "nombre": n, "partido": pa, "color": c,
        "votos": int(votos * v / 100.0), "porcentaje": v,
    } for (n, pa, c, v) in _SIM]
    cands.sort(key=lambda x: x["votos"], reverse=True)
    return {
        "eleccion": "Presidencia de la República 2026 — Primera vuelta",
        "fecha_jornada": "2026-05-31",
        "boletin": max(1, int(pct // 2) + 1),
        "fecha_corte_txt": time.strftime("%d/%m/%Y %H:%M"),
        "mesas_informadas": mesas,
        "mesas_total": MESAS_TOTAL_DEF,
        "porcentaje_mesas": pct,
        "votos_totales": votos,
        "participacion_pct": round(votos / CENSO_DEF * 100, 2),
        "abstencion": CENSO_DEF - votos,
        "abstencion_pct": round(100 - votos / CENSO_DEF * 100, 2),
        "censo": CENSO_DEF,
        "desglose": {
            "validos": int(votos * 0.98), "validos_pct": 98.0,
            "blanco": int(votos * 0.018), "blanco_pct": 1.8,
            "nulos": int(votos * 0.01), "nulos_pct": 1.0,
            "no_marcados": int(votos * 0.002), "no_marcados_pct": 0.2,
        },
        "comparativo": {
            "cepeda": {"votos": int(votos * 0.315), "pct": 31.5},
            "abelardo": {"votos": int(votos * 0.24), "pct": 24.0},
            "paloma": {"votos": int(votos * 0.185), "pct": 18.5},
            "suma": {"votos": int(votos * 0.425), "pct": 42.5},
        },
        "fuente": "SIMULACIÓN",
        "fuente_nota": ("Datos de avance SIMULADOS (la lista de candidatos es real; "
                        "los votos no son oficiales). " + nota_extra).strip(),
        "fuente_url": FUENTE_PORTAL,
        "candidatos": cands,
    }


SERIE_FILE = BASE_DIR / "data" / "serie.json"


def _registrar_serie(datos):
    """Guarda un punto de la serie temporal por boletín (para la línea de tiempo).

    El feed público no expone el histórico por candidato, así que registramos en
    vivo: un punto por cada boletín nuevo. Captura toda la noche de la 2.ª vuelta.
    """
    if not str(datos.get("fuente", "")).startswith("OFICIAL"):
        return
    try:
        serie = json.loads(SERIE_FILE.read_text("utf-8")) if SERIE_FILE.exists() else []
    except Exception:
        serie = []
    if serie and serie[-1].get("boletin") == datos.get("boletin"):
        return                                   # boletín ya registrado
    def pctof(frag):
        for c in datos.get("candidatos", []):
            if frag.lower() in c["nombre"].lower():
                return c["porcentaje"]
        return 0
    serie.append({
        "boletin": datos.get("boletin"),
        "corte": datos.get("fecha_corte_txt"),
        "mesas_pct": datos.get("porcentaje_mesas"),
        "abelardo": pctof("Espriella"),
        "cepeda": pctof("Cepeda"),
        "paloma": pctof("Valencia"),
    })
    serie = serie[-500:]
    try:
        SERIE_FILE.parent.mkdir(exist_ok=True)
        SERIE_FILE.write_text(json.dumps(serie, ensure_ascii=False), "utf-8")
    except Exception:
        pass


def obtener_resultados():
    """Feed OFICIAL si responde; si no, simulación de respaldo."""
    try:
        raw = _fetch_json(OFICIAL_URL, timeout=10, bust=True)
        datos = _normalizar_oficial(raw)
        if datos["candidatos"]:
            _registrar_serie(datos)
            return datos
        return _simular_avance("El feed oficial no traía candidatos aún.")
    except (urllib.error.URLError, json.JSONDecodeError, ValueError, KeyError) as e:
        return _simular_avance(f"Feed oficial no disponible ({type(e).__name__}). "
                               "Reintentando en cada actualización.")


# ---------------------------------------------------------------------------
# Asistente IA — proxy a Google Gemini (la API key queda solo en el servidor)
# ---------------------------------------------------------------------------
def responder_ia(pregunta, panel, contexto):
    """Consulta a Gemini con la pregunta del usuario + el contexto del panel."""
    pregunta = (pregunta or "").strip()[:600]
    panel = (panel or "Panel").strip()[:120]
    contexto = (contexto or "").strip()[:6000]
    if not pregunta:
        return {"ok": False, "error": "Pregunta vacía"}
    if not GEMINI_API_KEY:
        return {"ok": False, "error": "Falta GEMINI_API_KEY en el servidor"}

    texto = (f"PANEL: {panel}\n\n{contexto}\n\n"
             f"PREGUNTA DEL USUARIO: {pregunta}")
    payload = {
        "systemInstruction": {"parts": [{"text": IA_SISTEMA}]},
        "contents": [{"role": "user", "parts": [{"text": texto}]}],
        # thinkingBudget=0 desactiva el "razonamiento" del modelo: si no, esos
        # tokens consumen el presupuesto y la respuesta sale truncada (MAX_TOKENS).
        "generationConfig": {"temperature": 0.3, "maxOutputTokens": 1200,
                             "thinkingConfig": {"thinkingBudget": 0}},
    }
    req = urllib.request.Request(
        f"{GEMINI_URL}?key={GEMINI_API_KEY}",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30, context=_SSL) as r:
            data = json.loads(r.read().decode("utf-8"))
        cand = (data.get("candidates") or [{}])[0]
        partes = (cand.get("content") or {}).get("parts") or []
        respuesta = "".join(p.get("text", "") for p in partes).strip()
        if not respuesta:
            return {"ok": False, "error": "Respuesta vacía del modelo"}
        return {"ok": True, "answer": respuesta}
    except urllib.error.HTTPError as e:
        detalle = ""
        try:
            detalle = json.loads(e.read().decode("utf-8")).get("error", {}).get("message", "")
        except Exception:
            pass
        return {"ok": False, "error": f"Gemini {e.code}: {detalle or e.reason}"}
    except Exception as e:  # pragma: no cover
        return {"ok": False, "error": f"{type(e).__name__}: {e}"}


# ---------------------------------------------------------------------------
# Servidor HTTP
# ---------------------------------------------------------------------------
class Handler(BaseHTTPRequestHandler):
    def _send(self, code, body, content_type="text/html; charset=utf-8"):
        if isinstance(body, str):
            body = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_POST(self):
        path = self.path.split("?", 1)[0]
        if path == "/api/chat":
            try:
                largo = int(self.headers.get("Content-Length", 0))
                data = json.loads(self.rfile.read(largo).decode("utf-8")) if largo else {}
                res = responder_ia(data.get("question"), data.get("panel"),
                                   data.get("context"))
                code = 200 if res.get("ok") else 502
                self._send(code, json.dumps(res, ensure_ascii=False),
                           "application/json; charset=utf-8")
            except Exception as e:  # pragma: no cover
                self._send(500, json.dumps({"ok": False, "error": str(e)}),
                           "application/json; charset=utf-8")
            return
        self._send(404, json.dumps({"ok": False, "error": "No encontrado"}),
                   "application/json; charset=utf-8")

    def do_GET(self):
        path = self.path.split("?", 1)[0]

        if path == "/api/resultados":
            try:
                payload = obtener_resultados()
                self._send(200, json.dumps(payload, ensure_ascii=False),
                           "application/json; charset=utf-8")
            except Exception as e:  # pragma: no cover
                self._send(500, json.dumps({"error": str(e)}),
                           "application/json; charset=utf-8")
            return

        if path == "/api/ciudades":
            try:
                payload = obtener_ciudades()
                self._send(200, json.dumps(payload, ensure_ascii=False),
                           "application/json; charset=utf-8")
            except Exception as e:  # pragma: no cover
                self._send(500, json.dumps({"error": str(e)}),
                           "application/json; charset=utf-8")
            return

        if path == "/api/departamentos":
            try:
                payload = obtener_departamentos()
                self._send(200, json.dumps(payload, ensure_ascii=False),
                           "application/json; charset=utf-8")
            except Exception as e:  # pragma: no cover
                self._send(500, json.dumps({"error": str(e)}),
                           "application/json; charset=utf-8")
            return

        if path == "/api/serie":
            try:
                serie = json.loads(SERIE_FILE.read_text("utf-8")) if SERIE_FILE.exists() else []
            except Exception:
                serie = []
            self._send(200, json.dumps({"serie": serie}, ensure_ascii=False),
                       "application/json; charset=utf-8")
            return

        if path == "/api/exterior":
            try:
                payload = obtener_exterior()
                self._send(200, json.dumps(payload, ensure_ascii=False),
                           "application/json; charset=utf-8")
            except Exception as e:  # pragma: no cover
                self._send(500, json.dumps({"error": str(e)}),
                           "application/json; charset=utf-8")
            return

        if path == "/api/municipios":
            try:
                dep = (parse_qs(urlparse(self.path).query).get("dep") or [""])[0]
                payload = obtener_municipios(dep) if dep else {"ok": False, "municipios": []}
                self._send(200, json.dumps(payload, ensure_ascii=False),
                           "application/json; charset=utf-8")
            except Exception as e:  # pragma: no cover
                self._send(500, json.dumps({"error": str(e)}),
                           "application/json; charset=utf-8")
            return

        if path == "/api/polymarket":
            try:
                payload = obtener_polymarket()
                self._send(200, json.dumps(payload, ensure_ascii=False),
                           "application/json; charset=utf-8")
            except Exception as e:  # pragma: no cover
                self._send(500, json.dumps({"error": str(e)}),
                           "application/json; charset=utf-8")
            return

        if path == "/":
            path = "/index.html"
        archivo = (WEB_DIR / path.lstrip("/")).resolve()
        if not str(archivo).startswith(str(WEB_DIR)) or not archivo.is_file():
            self._send(404, "No encontrado")
            return

        tipos = {".html": "text/html; charset=utf-8", ".css": "text/css; charset=utf-8",
                 ".js": "application/javascript; charset=utf-8",
                 ".json": "application/json; charset=utf-8",
                 ".geojson": "application/geo+json; charset=utf-8", ".svg": "image/svg+xml"}
        self._send(200, archivo.read_bytes(),
                   tipos.get(archivo.suffix, "application/octet-stream"))

    def log_message(self, *a):
        pass


def main():
    # En Windows la consola suele ser cp1252 y el banner (con caracteres como
    # «─») rompería con UnicodeEncodeError. Forzamos UTF-8 en la salida.
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except Exception:
            pass

    server = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    print("─" * 64)
    print("  Dashboard Elecciones Presidenciales Colombia 2026")
    print("  Primera vuelta · 31 de mayo de 2026")
    print("─" * 64)
    print(f"  Feed oficial : {OFICIAL_URL}")
    print(f"  Servidor     : http://localhost:{PORT}")
    print("  Detener      : Ctrl + C")
    print("─" * 64)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor detenido.")
        server.server_close()


if __name__ == "__main__":
    main()
