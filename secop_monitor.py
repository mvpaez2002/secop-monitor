"""
SECOP II Monitor — GitHub Actions
==================================
Consulta contratos y licitaciones de datos.gov.co
y envía el informe HTML a múltiples destinatarios por Gmail.

Variables de entorno requeridas (configuradas como GitHub Secrets):
  GMAIL_REMITENTE  → tu cuenta Gmail que envía
  GMAIL_PASSWORD   → contraseña de aplicación Gmail (16 caracteres)
  DESTINATARIOS    → correos separados por coma: a@x.com,b@y.com,c@z.com
"""

import os
import smtplib
import sys
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

try:
    import requests
except ImportError:
    print("Falta: pip install requests")
    sys.exit(1)

# ════════════════════════════════════════════════
#  CONFIGURACIÓN DE FILTROS — edita aquí
# ════════════════════════════════════════════════

FILTROS = {
    "departamento": "",     # Ej: "Cundinamarca" — vacío = toda Colombia
    "sector":       "",     # Ej: "salud", "obras", "tecnología" — vacío = todos
    "dias":         1,      # Contratos firmados en los últimos N días
    "dias_licit":   30,     # Licitaciones publicadas en los últimos N días
    "limite":       50,     # Máx. registros por consulta
}

# ════════════════════════════════════════════════

BASE_CONTRATOS  = "https://www.datos.gov.co/resource/jbjy-vk9h.json"
BASE_LICITACION = "https://www.datos.gov.co/resource/p6dx-8zbt.json"
HEADERS = {"Accept": "application/json"}


# ── Helpers ────────────────────────────────────────────────────────────────────

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)


def fmt_cop(valor):
    try:
        n = float(valor)
    except (TypeError, ValueError):
        return "N/D"
    if n >= 1_000_000_000:
        return f"${n/1_000_000_000:.1f}B"
    if n >= 1_000_000:
        return f"${n/1_000_000:.0f}M"
    if n >= 1_000:
        return f"${n/1_000:.0f}K"
    return f"${n:,.0f}"


def fmt_fecha(s):
    if not s:
        return "—"
    try:
        return datetime.fromisoformat(s[:19]).strftime("%d/%m/%Y")
    except Exception:
        return s[:10]


# ── Consultas API ──────────────────────────────────────────────────────────────

def consultar_api(url, where, order, limite):
    try:
        r = requests.get(
            url,
            params={"$where": where, "$order": order, "$limit": limite},
            headers=HEADERS,
            timeout=30,
        )
        r.raise_for_status()
        return r.json()
    except Exception as e:
        log(f"Error API ({url}): {e}")
        return []


def obtener_contratos():
    f = FILTROS
    fecha = (datetime.now() - timedelta(days=f["dias"])).strftime("%Y-%m-%dT00:00:00.000")
    cond = [f"fecha_de_firma >= '{fecha}'"]
    if f["departamento"]:
        cond.append(f"upper(departamento) LIKE upper('%{f['departamento']}%')")
    if f["sector"]:
        cond.append(f"upper(objeto_del_contrato) LIKE upper('%{f['sector']}%')")
    return consultar_api(BASE_CONTRATOS, " AND ".join(cond), "valor_del_contrato DESC", f["limite"])


def obtener_licitaciones():
    f = FILTROS
    fecha = (datetime.now() - timedelta(days=f["dias_licit"])).strftime("%Y-%m-%dT00:00:00.000")
    cond = [
        "estado_del_proceso='Convocado'",
        f"fecha_de_publicacion_del >= '{fecha}'",
    ]
    if f["departamento"]:
        cond.append(f"upper(departamento_entidad) LIKE upper('%{f['departamento']}%')")
    if f["sector"]:
        cond.append(f"upper(descripci_n_del_procedimiento) LIKE upper('%{f['sector']}%')")
    return consultar_api(BASE_LICITACION, " AND ".join(cond), "precio_base DESC", f["limite"])


# ── Generador HTML ─────────────────────────────────────────────────────────────

def generar_html(contratos, licitaciones):
    f = FILTROS
    hoy      = datetime.now().strftime("%d de %B de %Y, %H:%M UTC")
    hoy_co   = datetime.now().strftime("%d/%m/%Y")
    total    = sum(float(c.get("valor_del_contrato") or 0) for c in contratos)
    entidades = len(set(c.get("nombre_entidad", "") for c in contratos))

    def fila_c(c):
        return (
            f"<tr>"
            f"<td>{c.get('nombre_entidad','—')}</td>"
            f"<td>{(c.get('objeto_del_contrato') or '—')[:100]}</td>"
            f"<td style='text-align:right;white-space:nowrap'>{fmt_cop(c.get('valor_del_contrato'))}</td>"
            f"<td>{(c.get('proveedor_adjudicado') or '—')[:50]}</td>"
            f"<td style='white-space:nowrap'>{fmt_fecha(c.get('fecha_de_firma'))}</td>"
            f"<td>{(c.get('tipo_de_contrato') or '—')[:30]}</td>"
            f"</tr>"
        )

    def fila_l(l):
        return (
            f"<tr>"
            f"<td>{l.get('nombre_entidad','—')}</td>"
            f"<td>{(l.get('descripci_n_del_procedimiento') or '—')[:100]}</td>"
            f"<td style='text-align:right;white-space:nowrap'>{fmt_cop(l.get('precio_base'))}</td>"
            f"<td>{(l.get('modalidad_de_contratacion') or '—')[:40]}</td>"
            f"<td style='white-space:nowrap'>{fmt_fecha(l.get('fecha_de_publicacion_del'))}</td>"
            f"</tr>"
        )

    filas_c = "".join(fila_c(c) for c in contratos[:30]) or \
              "<tr><td colspan='6' style='text-align:center;color:#888;padding:20px'>Sin contratos en este período</td></tr>"

    filas_l = "".join(fila_l(l) for l in licitaciones[:20]) or \
              "<tr><td colspan='5' style='text-align:center;color:#888;padding:20px'>Sin licitaciones abiertas</td></tr>"

    depto_txt  = f["departamento"] or "Colombia"
    sector_txt = f["sector"] or "Todos"

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Informe SECOP II — {hoy_co}</title>
<style>
  *{{box-sizing:border-box}}
  body{{margin:0;padding:0;background:#f0f2f7;font-family:Segoe UI,Arial,sans-serif;font-size:13px;color:#1a1a2e}}
  .wrap{{max-width:980px;margin:24px auto;background:#fff;border-radius:12px;overflow:hidden;box-shadow:0 4px 20px rgba(0,0,0,.1)}}
  .top{{background:linear-gradient(135deg,#1a3c6e,#2c6faf);color:#fff;padding:28px 32px}}
  .top h1{{margin:0 0 6px;font-size:22px;font-weight:600}}
  .top .meta{{opacity:.8;font-size:12px}}
  .body{{padding:28px 32px}}
  .metrics{{display:flex;gap:12px;flex-wrap:wrap;margin-bottom:28px}}
  .m{{flex:1;min-width:110px;background:#f0f5ff;border:1px solid #ccd9f5;border-radius:10px;padding:14px 18px;text-align:center}}
  .m .v{{font-size:24px;font-weight:700;color:#1a3c6e;line-height:1.2}}
  .m .l{{font-size:11px;color:#556;margin-top:4px;text-transform:uppercase;letter-spacing:.04em}}
  h2{{color:#1a3c6e;font-size:15px;margin:28px 0 10px;padding-bottom:6px;border-bottom:2px solid #e0e8f7}}
  table{{width:100%;border-collapse:collapse;font-size:12px}}
  th{{background:#1a3c6e;color:#fff;padding:8px 10px;text-align:left;font-size:11px;text-transform:uppercase;letter-spacing:.05em;font-weight:500}}
  td{{padding:7px 10px;border-bottom:1px solid #eef0f7;vertical-align:top}}
  tr:last-child td{{border-bottom:none}}
  tr:nth-child(even) td{{background:#f8faff}}
  tr:hover td{{background:#edf2ff}}
  .footer{{background:#f8f9fc;border-top:1px solid #e5e8f0;padding:14px 32px;font-size:11px;color:#999;text-align:center}}
  @media(max-width:600px){{
    .body{{padding:16px}}
    .top{{padding:20px 16px}}
    table{{font-size:11px}}
    th,td{{padding:5px 6px}}
  }}
</style>
</head>
<body>
<div class="wrap">
  <div class="top">
    <h1>📋 Informe SECOP II</h1>
    <div class="meta">
      {hoy} &nbsp;·&nbsp; Departamento: <b>{depto_txt}</b>
      &nbsp;·&nbsp; Sector: <b>{sector_txt}</b>
      &nbsp;·&nbsp; Contratos últimos <b>{f['dias']}</b> día(s)
    </div>
  </div>

  <div class="body">
    <div class="metrics">
      <div class="m"><div class="v">{len(contratos)}</div><div class="l">Contratos</div></div>
      <div class="m"><div class="v">{len(licitaciones)}</div><div class="l">Licitaciones</div></div>
      <div class="m"><div class="v">{fmt_cop(total)}</div><div class="l">Valor total</div></div>
      <div class="m"><div class="v">{entidades}</div><div class="l">Entidades</div></div>
    </div>

    <h2>🔔 Licitaciones abiertas ({len(licitaciones)})</h2>
    <table>
      <tr>
        <th>Entidad</th>
        <th>Descripción</th>
        <th>Presupuesto</th>
        <th>Modalidad</th>
        <th>Publicación</th>
      </tr>
      {filas_l}
    </table>

    <h2>📝 Contratos recientes ({len(contratos)})</h2>
    <table>
      <tr>
        <th>Entidad</th>
        <th>Objeto</th>
        <th>Valor</th>
        <th>Contratista</th>
        <th>Firma</th>
        <th>Tipo</th>
      </tr>
      {filas_c}
    </table>
  </div>

  <div class="footer">
    Fuente: SECOP II · datos.gov.co · Colombia Compra Eficiente<br>
    Informe automático generado por GitHub Actions
  </div>
</div>
</body>
</html>"""


# ── Envío de correo ────────────────────────────────────────────────────────────

def enviar_correo(html, contratos, licitaciones):
    remitente    = os.environ.get("GMAIL_REMITENTE", "").strip()
    password     = os.environ.get("GMAIL_PASSWORD", "").strip()
    destinatarios_raw = os.environ.get("DESTINATARIOS", "").strip()

    if not remitente or not password or not destinatarios_raw:
        log("⚠️  Variables de entorno faltantes: GMAIL_REMITENTE, GMAIL_PASSWORD o DESTINATARIOS")
        log("   Configúralas como GitHub Secrets en tu repositorio.")
        return

    # Parsear lista de destinatarios (separados por coma)
    destinatarios = [d.strip() for d in destinatarios_raw.split(",") if d.strip()]
    if not destinatarios:
        log("⚠️  No hay destinatarios configurados.")
        return

    hoy = datetime.now().strftime("%d/%m/%Y")
    asunto = (f"📋 Informe SECOP {hoy} — "
              f"{len(contratos)} contratos · {len(licitaciones)} licitaciones")

    log(f"Enviando a {len(destinatarios)} destinatario(s)...")

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(remitente, password)
            for dest in destinatarios:
                msg = MIMEMultipart("alternative")
                msg["Subject"] = asunto
                msg["From"]    = f"Monitor SECOP <{remitente}>"
                msg["To"]      = dest
                msg.attach(MIMEText(html, "html", "utf-8"))
                server.sendmail(remitente, dest, msg.as_string())
                log(f"  ✅ Enviado a {dest}")
    except smtplib.SMTPAuthenticationError:
        log("❌ Error de autenticación Gmail.")
        log("   Asegúrate de usar una 'Contraseña de aplicación', no tu contraseña normal.")
        log("   Genera una en: https://myaccount.google.com/apppasswords")
        sys.exit(1)
    except Exception as e:
        log(f"❌ Error al enviar correo: {e}")
        sys.exit(1)


# ── Guardar HTML localmente ────────────────────────────────────────────────────

def guardar_html(html):
    nombre = f"informe_secop_{datetime.now().strftime('%Y-%m-%d')}.html"
    Path(nombre).write_text(html, encoding="utf-8")
    log(f"HTML guardado: {nombre}")
    return nombre


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    log("=" * 50)
    log("SECOP Monitor — GitHub Actions")
    log(f"Filtros: depto={FILTROS['departamento'] or 'todos'} | "
        f"sector={FILTROS['sector'] or 'todos'} | "
        f"dias={FILTROS['dias']}")
    log("=" * 50)

    log("Consultando contratos...")
    contratos = obtener_contratos()
    log(f"  → {len(contratos)} contratos encontrados")

    log("Consultando licitaciones...")
    licitaciones = obtener_licitaciones()
    log(f"  → {len(licitaciones)} licitaciones encontradas")

    log("Generando HTML...")
    html = generar_html(contratos, licitaciones)
    guardar_html(html)

    log("Enviando correos...")
    enviar_correo(html, contratos, licitaciones)

    log("=" * 50)
    log("✅ Finalizado correctamente")


if __name__ == "__main__":
    main()
