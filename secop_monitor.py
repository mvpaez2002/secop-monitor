import os
import smtplib
import requests
import html

from datetime import datetime, timedelta
from pathlib import Path

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


# ==========================================================
# CONFIGURACIÓN GENERAL
# ==========================================================

API_SECOP = "https://www.datos.gov.co/resource/p6dx-8zbt.json"

DIAS_BUSQUEDA = 180

MAX_RESULTADOS_API = 1000

MAX_INFORME = 150



# ==========================================================
# PALABRAS CLAVE SEGURIDAD TECNOLÓGICA
# ==========================================================

PALABRAS_CLAVE = [

    # SOC / SIEM / Ciberseguridad
    "soc",
    "centro de operaciones de seguridad",
    "centro operaciones seguridad",
    "siem",
    "ciberseguridad",
    "seguridad informática",
    "seguridad informatica",
    "seguridad de la información",
    "seguridad informacion",
    "monitoreo seguridad",
    "correlación de eventos",
    "gestión de eventos",
    "respuesta incidentes",


    # Centros de control
    "centro de control",
    "centro integrado de control",
    "centro integrado de operaciones",
    "centro de monitoreo",
    "sala de monitoreo",
    "sala de control",
    "centro de comando",
    "centro comando",
    "c4",
    "c5",
    "c2",


    # CCTV / Video seguridad
    "cctv",
    "circuito cerrado televisión",
    "circuito cerrado de television",
    "videovigilancia",
    "video vigilancia",
    "cámaras",
    "camaras",
    "camara ip",
    "cámara ip",
    "video analítica",
    "analitica de video",
    "analítica de video",
    "vms",
    "grabador",
    "nvr",
    "dvr",


    # Fabricantes seguridad electrónica
    "hikvision",
    "dahua",
    "axis",
    "bosch",
    "milestone",
    "genetec",
    "avigilon",
    "hanwha",


    # Control acceso
    "control de acceso",
    "control acceso",
    "biometría",
    "biometria",
    "huella digital",
    "reconocimiento facial",
    "facial",
    "torniquetes",
    "lector biométrico",


    # Redes seguridad
    "firewall",
    "fortinet",
    "fortigate",
    "checkpoint",
    "palo alto",
    "sonicwall",
    "proxy",
    "vpn",
    "ips",
    "ids",


    # Infraestructura
    "data center",
    "centro de datos",
    "servidores",
    "storage",
    "almacenamiento",
    "backup",
    "respaldo",
    "san",
    "nas",


    # Cloud
    "cloud",
    "nube",
    "aws",
    "azure",
    "google cloud",
    "virtualización",
    "virtualizacion",


    # Redes
    "redes",
    "switch",
    "router",
    "wifi",
    "lan",
    "wan",


    # Software
    "software",
    "licenciamiento",
    "firma digital",
    "certificado digital",
    "gestión documental",

]



# ==========================================================
# UNSPSC TECNOLOGÍA
# ==========================================================

CODIGOS_UNSPSC = {

    "4323": "Software",

    "432332": "Software seguridad",

    "4322": "Redes comunicaciones",

    "4321": "Hardware",

    "4320": "Tecnología informática",

    "8111": "Servicios TI",

    "4617": "Seguridad electrónica",

    "461716": "Videovigilancia",

    "4618": "Control acceso"

}



# ==========================================================
# LOG
# ==========================================================

def log(texto):

    print(
        f"[{datetime.now().strftime('%H:%M:%S')}] {texto}",
        flush=True
    )



# ==========================================================
# CONSULTA SECOP
# ==========================================================

def consultar_secop():


    fecha = (

        datetime.now()
        -
        timedelta(days=DIAS_BUSQUEDA)

    ).strftime(
        "%Y-%m-%dT00:00:00.000"
    )



    consultas = [

        "seguridad",

        "ciberseguridad",

        "soc",

        "siem",

        "monitoreo",

        "centro control",

        "cctv",

        "camaras",

        "videovigilancia",

        "firewall",

        "redes",

        "software",

        "servidores",

        "cloud",

        "biometria",

        "control acceso",

        "data center"

    ]



    resultados = []



    for palabra in consultas:


        log(
            f"Buscando: {palabra}"
        )


        try:


            respuesta = requests.get(

                API_SECOP,

                params={

                    "$limit": MAX_RESULTADOS_API,

                    "$q": palabra,

                    "$where":
                    f"fecha_de_publicacion_del >= '{fecha}'"

                },

                timeout=90

            )



            respuesta.raise_for_status()



            datos = respuesta.json()



            log(
                f"{palabra}: {len(datos)} registros"
            )



            resultados.extend(datos)



        except Exception as e:


            log(
                f"Error {palabra}: {e}"
            )



    return eliminar_duplicados(resultados)



# ==========================================================
# QUITAR DUPLICADOS
# ==========================================================

def eliminar_duplicados(datos):


    vistos = set()

    salida = []



    for item in datos:


        identificador = (

            item.get(
                "id_del_proceso",
                ""
            )

            or

            item.get(
                "referencia_del_proceso",
                ""
            )

        )



        if identificador not in vistos:


            vistos.add(
                identificador
            )


            salida.append(
                item
            )



    return salida



# ==========================================================
# ANALIZAR OPORTUNIDAD
# ==========================================================

def analizar_registro(registro):


    texto = " ".join([


        str(registro.get(
            "nombre_del_procedimiento",
            ""
        )),


        str(registro.get(
            "descripci_n_del_procedimiento",
            ""
        )),


        str(registro.get(
            "codigo_principal_de_categoria",
            ""
        )),


        str(registro.get(
            "categorias_adicionales",
            ""
        ))

    ]).lower()



    puntos = 0

    motivos = []



    for palabra in PALABRAS_CLAVE:


        if palabra.lower() in texto:


            puntos += 10

            motivos.append(
                palabra
            )



    codigo = str(

        registro.get(
            "codigo_principal_de_categoria",
            ""
        )

    )



    for clave, nombre in CODIGOS_UNSPSC.items():


        if clave in codigo:


            puntos += 25

            motivos.append(
                nombre
            )



    # Prioridad alta

    if "cctv" in texto or "videovigilancia" in texto:

        puntos += 20



    if "soc" in texto or "siem" in texto:

        puntos += 30



    if "centro de control" in texto:

        puntos += 25



    return puntos, list(set(motivos))



# ==========================================================
# FILTRAR
# ==========================================================

def filtrar(datos):


    encontrados = []



    for registro in datos:


        puntos, motivos = analizar_registro(
            registro
        )


        if puntos >= 30:


            registro["puntaje"] = puntos

            registro["motivos"] = ", ".join(
                motivos
            )


            encontrados.append(
                registro
            )



    encontrados.sort(

        key=lambda x:x["puntaje"],

        reverse=True

    )

    return encontrados


# ==========================================================
# FORMATO DINERO
# ==========================================================

def dinero(valor):

    try:

        numero = float(valor)

        return "$ {:,.0f}".format(numero)

    except:

        return "-"



# ==========================================================
# NIVEL DE ALERTA
# ==========================================================

def nivel(puntos):

    if puntos >= 80:
        return "CRÍTICO"

    elif puntos >= 50:
        return "ALTO"

    else:
        return "MEDIO"



# ==========================================================
# GENERAR HTML DASHBOARD
# ==========================================================

def generar_html(datos):


    filas = ""



    for r in datos[:MAX_INFORME]:


        entidad = (

            r.get(
                "entidad",
                "-"
            )

        )


        descripcion = (

            r.get(
                "descripci_n_del_procedimiento",
                "-"
            )

        )


        valor = (

            r.get(
                "precio_base",
                "0"
            )

        )


        puntaje = r.get(
            "puntaje",
            0
        )



        color = (

            "#dc2626"
            if puntaje >= 80

            else

            "#f59e0b"
            if puntaje >= 50

            else

            "#2563eb"

        )



        link = ""

        url = r.get(
            "urlproceso",
            ""
        )


        if isinstance(url, dict):

            link = url.get(
                "url",
                ""
            )



        filas += f"""
<tr>
  <td style="padding:12px;border-bottom:1px solid #e2e8f0;font-size:13px;font-family:Arial,sans-serif;color:#1e293b;">
    <b>{html.escape(str(entidad))}</b>
  </td>
  <td style="padding:12px;border-bottom:1px solid #e2e8f0;font-size:13px;font-family:Arial,sans-serif;color:#1e293b;">
    {html.escape(str(descripcion)[:350])}
  </td>
  <td style="padding:12px;border-bottom:1px solid #e2e8f0;font-size:13px;font-family:Arial,sans-serif;color:#1e293b;">
    {dinero(valor)}
  </td>
  <td style="padding:12px;border-bottom:1px solid #e2e8f0;font-size:13px;font-family:Arial,sans-serif;color:#1e293b;">
    <table role="presentation" cellpadding="0" cellspacing="0" border="0">
      <tr>
        <td style="background-color:{color};color:#ffffff;padding:5px 10px;font-family:Arial,sans-serif;font-size:12px;">
          {puntaje} puntos
        </td>
      </tr>
    </table>
    <div style="font-size:11px;color:#475569;margin-top:4px;">{nivel(puntaje)}</div>
  </td>
  <td style="padding:12px;border-bottom:1px solid #e2e8f0;font-size:13px;font-family:Arial,sans-serif;color:#1e293b;">
    {html.escape(str(r.get("motivos","")))}
  </td>
  <td style="padding:12px;border-bottom:1px solid #e2e8f0;font-size:13px;font-family:Arial,sans-serif;">
    <a target="_blank" href="{link}" style="color:#2563eb;font-weight:bold;text-decoration:underline;">Abrir SECOP</a>
  </td>
</tr>
"""



    if not filas:


        filas = """
<tr>
  <td colspan="6" style="padding:20px;text-align:center;font-family:Arial,sans-serif;">
    <h3 style="margin:0;color:#1e293b;">No se encontraron oportunidades</h3>
  </td>
</tr>
"""



    fecha = datetime.now().strftime(
        "%d/%m/%Y %H:%M"
    )


    def tarjeta(valor, etiqueta):
        return f"""
<td width="25%" style="padding:8px;" valign="top">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="background-color:#ffffff;border:1px solid #e2e8f0;">
    <tr>
      <td style="padding:20px;font-family:Arial,sans-serif;">
        <div style="font-size:30px;font-weight:bold;color:#1d4ed8;line-height:1.2;">{valor}</div>
        <div style="font-size:13px;color:#1e293b;margin-top:4px;">{etiqueta}</div>
      </td>
    </tr>
  </table>
</td>
"""


    return f"""<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:v="urn:schemas-microsoft-com:vml" xmlns:o="urn:schemas-microsoft-com:office:office">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<!--[if mso]>
<noscript>
<xml>
<o:OfficeDocumentSettings>
<o:PixelsPerInch>96</o:PixelsPerInch>
</o:OfficeDocumentSettings>
</xml>
</noscript>
<![endif]-->
<title>Monitor SECOP Seguridad</title>
<style>
  body, table, td {{ font-family: Arial, "Segoe UI", sans-serif; }}
  body {{ margin:0; padding:0; background-color:#eef2ff; color:#1e293b; }}
  a {{ color:#2563eb; font-weight:bold; }}
  @media only screen and (max-width: 600px) {{
    .stack-card {{ display:block !important; width:100% !important; }}
  }}
</style>
</head>
<body style="margin:0;padding:0;background-color:#eef2ff;">

<!-- wrapper -->
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="background-color:#eef2ff;">
<tr>
<td align="center" style="padding:20px 10px;">

<!-- content, fixed width so Outlook doesn't stretch it -->
<table role="presentation" width="700" cellpadding="0" cellspacing="0" border="0" style="width:700px;max-width:700px;background-color:#eef2ff;">

<!-- header (solid color instead of gradient, Outlook doesn't render linear-gradient) -->
<tr>
<td style="background-color:#1d4ed8;padding:30px 35px;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">
    <tr>
      <td>
        <div style="font-family:Arial,sans-serif;color:#ffffff;font-size:28px;font-weight:bold;">
          &#128737; Monitor SECOP Seguridad Tecnol&oacute;gica
        </div>
        <div style="font-family:Arial,sans-serif;color:#dbe4ff;font-size:13px;margin-top:8px;">
          Centros de control | SOC | SIEM | CCTV | Ciberseguridad | Infraestructura TI
        </div>
        <div style="font-family:Arial,sans-serif;color:#dbe4ff;font-size:12px;margin-top:6px;">
          Generado: {fecha}
        </div>
      </td>
    </tr>
  </table>
</td>
</tr>

<!-- cards row (table-based, not flexbox) -->
<tr>
<td style="padding:15px 20px;background-color:#eef2ff;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">
    <tr>
      {tarjeta(len(datos), "Oportunidades detectadas")}
      {tarjeta(sum(1 for x in datos if x.get("puntaje",0)>=80), "Alertas cr&iacute;ticas")}
      {tarjeta(sum(1 for x in datos if "cctv" in str(x.get("motivos","")).lower()), "CCTV / Video seguridad")}
      {tarjeta(sum(1 for x in datos if "soc" in str(x.get("motivos","")).lower()), "SOC / SIEM")}
    </tr>
  </table>
</td>
</tr>

<!-- table container -->
<tr>
<td style="padding:15px 20px 30px 20px;background-color:#eef2ff;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="background-color:#ffffff;border:1px solid #e2e8f0;">
    <tr>
      <th align="left" style="background-color:#0f172a;color:#ffffff;padding:12px;font-family:Arial,sans-serif;font-size:13px;">Entidad</th>
      <th align="left" style="background-color:#0f172a;color:#ffffff;padding:12px;font-family:Arial,sans-serif;font-size:13px;">Descripci&oacute;n</th>
      <th align="left" style="background-color:#0f172a;color:#ffffff;padding:12px;font-family:Arial,sans-serif;font-size:13px;">Valor</th>
      <th align="left" style="background-color:#0f172a;color:#ffffff;padding:12px;font-family:Arial,sans-serif;font-size:13px;">Nivel</th>
      <th align="left" style="background-color:#0f172a;color:#ffffff;padding:12px;font-family:Arial,sans-serif;font-size:13px;">Detectado</th>
      <th align="left" style="background-color:#0f172a;color:#ffffff;padding:12px;font-family:Arial,sans-serif;font-size:13px;">Enlace</th>
    </tr>
    {filas}
  </table>
</td>
</tr>

</table>
<!-- /content -->

</td>
</tr>
</table>
<!-- /wrapper -->

</body>
</html>
"""



# ==========================================================
# GUARDAR INFORME
# ==========================================================

def guardar_archivo(contenido):


    nombre = (

        "SECOP_SEGURIDAD_"

        +

        datetime.now().strftime(
            "%Y%m%d_%H%M"
        )

        +

        ".html"

    )



    Path(nombre).write_text(

        contenido,

        encoding="utf-8"

    )


    log(
        f"HTML generado: {nombre}"
    )



# ==========================================================
# ENVIO EMAIL
# ==========================================================

def enviar_correo(html_text):


    remitente = os.getenv(
        "GMAIL_REMITENTE"
    )


    password = os.getenv(
        "GMAIL_PASSWORD"
    )


    destinatarios = os.getenv(
        "DESTINATARIOS"
    )



    if not remitente or not password or not destinatarios:


        log(
            "Correo no configurado"
        )

        return



    servidor = smtplib.SMTP_SSL(

        "smtp.gmail.com",

        465

    )



    servidor.login(

        remitente,

        password

    )



    for destino in destinatarios.split(","):


        mensaje = MIMEMultipart(
            "alternative"
        )


        mensaje["Subject"] = (

            "🛡️ Alertas SECOP Seguridad Tecnología"

        )


        mensaje["From"] = remitente

        mensaje["To"] = destino.strip()



        mensaje.attach(

            MIMEText(

                html_text,

                "html",

                "utf-8"

            )

        )



        servidor.sendmail(

            remitente,

            destino.strip(),

            mensaje.as_string()

        )



        log(
            f"Correo enviado: {destino}"
        )



    servidor.quit()



# ==========================================================
# MAIN
# ==========================================================

def main():


    log(
        "INICIANDO MONITOR SECOP"
    )


    datos = consultar_secop()



    log(
        f"Registros encontrados: {len(datos)}"
    )



    oportunidades = filtrar(
        datos
    )



    log(
        f"Oportunidades: {len(oportunidades)}"
    )



    informe = generar_html(
        oportunidades
    )



    guardar_archivo(
        informe
    )



    enviar_correo(
        informe
    )



    log(
        "PROCESO FINALIZADO"
    )




if __name__ == "__main__":

    main()
