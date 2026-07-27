import os
import smtplib
import requests

from datetime import datetime
from pathlib import Path

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


# ======================================================
# CONFIGURACIÓN
# ======================================================

LIMITE_API = 5000
LIMITE_INFORME = 100


API_PROCESOS = (
    "https://www.datos.gov.co/resource/p6dx-8zbt.json"
)

API_CONTRATOS = (
    "https://www.datos.gov.co/resource/jbjy-vk9h.json"
)


HEADERS = {
    "Accept": "application/json"
}



# ======================================================
# CATEGORÍAS TECNOLÓGICAS SECOP
# ======================================================

CODIGOS_TECNOLOGIA = {

    "432": "Tecnología informática",

    "4321": "Hardware",

    "4322": "Redes y comunicaciones",

    "4323": "Software",

    "8111": "Servicios TI",

    "811118": "Seguridad informática",

    "4617": "Seguridad electrónica",

    "81112": "Procesamiento de datos",

}



# ======================================================
# PALABRAS TECNOLÓGICAS
# ======================================================

PALABRAS_TECNOLOGIA = [

    "ciberseguridad",

    "seguridad informática",

    "seguridad informatica",

    "firewall",

    "siem",

    "soc",

    "centro de operaciones",

    "monitoreo",

    "centro de control",

    "cctv",

    "videovigilancia",

    "biometr",

    "facial",

    "reconocimiento",

    "abis",

    "verilook",

    "neurotechnology",

    "data center",

    "centro de datos",

    "servidores",

    "almacenamiento",

    "cloud",

    "nube",

    "aws",

    "azure",

    "inteligencia artificial",

    "analítica",

    "big data"

]



# ======================================================
# LOG
# ======================================================

def log(texto):

    print(
        f"[{datetime.now().strftime('%H:%M:%S')}] {texto}",
        flush=True
    )



# ======================================================
# CONSULTA SECOP
# ======================================================

def consultar_api(url):

    try:

        respuesta = requests.get(

            url,

            params={
                "$limit": LIMITE_API
            },

            headers=HEADERS,

            timeout=90

        )


        respuesta.raise_for_status()


        datos = respuesta.json()


        log(
            f"Registros recibidos: {len(datos)}"
        )


        if datos:

            log(
                "Campos detectados:"
            )

            print(
                list(datos[0].keys())
            )


        return datos


    except Exception as error:


        log(
            f"Error API: {error}"
        )


        return []



# ======================================================
# ANALIZAR CATEGORÍAS SECOP
# ======================================================

def analizar_tecnologia(registro):


    encontrados = []


    codigo = (

        str(
            registro.get(
                "codigo_principal_de_categoria",
                ""
            )
        )

        +

        " "

        +

        str(
            registro.get(
                "categorias_adicionales",
                ""
            )
        )

    ).lower()



    for clave, nombre in CODIGOS_TECNOLOGIA.items():

        if clave.lower() in codigo:

            encontrados.append(
                f"{clave} - {nombre}"
            )



    texto = str(registro).lower()



    for palabra in PALABRAS_TECNOLOGIA:


        if palabra in texto:


            encontrados.append(
                palabra
            )



    return list(
        set(encontrados)
    )



# ======================================================
# FILTRO
# ======================================================

def filtrar(registros):


    resultado = []


    for registro in registros:


        hallazgos = analizar_tecnologia(
            registro
        )


        if hallazgos:


            registro["hallazgos"] = (

                ", ".join(hallazgos)

            )


            resultado.append(
                registro
            )



    return resultado



# ======================================================
# OBTENER PROCESOS
# ======================================================

def obtener_procesos():


    log(
        "Consultando procesos..."
    )


    datos = consultar_api(
        API_PROCESOS
    )


    encontrados = filtrar(
        datos
    )


    log(
        f"Procesos encontrados: {len(encontrados)}"
    )


    return encontrados



# ======================================================
# OBTENER CONTRATOS
# ======================================================

def obtener_contratos():


    log(
        "Consultando contratos..."
    )


    datos = consultar_api(
        API_CONTRATOS
    )


    encontrados = filtrar(
        datos
    )


    log(
        f"Contratos encontrados: {len(encontrados)}"
    )


    return encontrados



# ======================================================
# FORMATO DINERO
# ======================================================

def dinero(valor):

    try:

        return (

            "${:,.0f}".format(
                float(valor)
            )

        )


    except:

        return "-"



# ======================================================
# HTML
# ======================================================

def generar_html(procesos, contratos):


    registros = (

        contratos

        +

        procesos

    )



    filas = ""



    for r in registros[:LIMITE_INFORME]:


        entidad = (

            r.get("entidad")

            or

            r.get("nombre_entidad")

            or

            "-"

        )


        descripcion = (

            r.get(
                "descripci_n_del_procedimiento"
            )

            or

            r.get(
                "objeto_del_contrato"
            )

            or

            "-"

        )


        valor = (

            r.get(
                "precio_base"
            )

            or

            r.get(
                "valor_del_contrato"
            )

            or

            0

        )


        filas += f"""

<tr>

<td>{entidad}</td>

<td>{str(descripcion)[:200]}</td>

<td>{dinero(valor)}</td>

<td>{r.get('codigo_principal_de_categoria','')}</td>

<td>{r.get('hallazgos','')}</td>

</tr>

"""



    if not filas:


        filas = """

<tr>

<td colspan="5">

No se encontraron oportunidades

</td>

</tr>

"""



    return f"""

<html>

<head>

<meta charset="utf-8">

<style>

body {{
font-family:Arial;
background:#eef2f7;
padding:20px;
}}

table {{
width:100%;
border-collapse:collapse;
background:white;
}}

th {{
background:#003566;
color:white;
padding:10px;
}}

td {{
padding:8px;
border-bottom:1px solid #ddd;
}}

</style>

</head>


<body>


<h1>
🛡️ Monitor SECOP Tecnología
</h1>


<p>
Fecha:
{datetime.now()}
</p>


<table>

<tr>

<th>Entidad</th>

<th>Descripción</th>

<th>Valor</th>

<th>UNSPSC</th>

<th>Detectado</th>

</tr>


{filas}


</table>


</body>

</html>

"""



# ======================================================
# GUARDAR
# ======================================================

def guardar(html):


    nombre = (

        "informe_secop_"

        +

        datetime.now().strftime(
            "%Y%m%d_%H%M"
        )

        +

        ".html"

    )


    Path(nombre).write_text(

        html,

        encoding="utf-8"

    )


    log(
        f"Generado: {nombre}"
    )



# ======================================================
# EMAIL
# ======================================================

def enviar_email(html):


    remitente = os.getenv(
        "GMAIL_REMITENTE"
    )


    password = os.getenv(
        "GMAIL_PASSWORD"
    )


    destinos = os.getenv(
        "DESTINATARIOS"
    )



    if not remitente or not password:

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



    for destino in destinos.split(","):


        msg = MIMEMultipart(
            "alternative"
        )


        msg["Subject"] = (
            "🛡️ Monitor SECOP Tecnología"
        )


        msg["From"] = remitente

        msg["To"] = destino.strip()



        msg.attach(

            MIMEText(

                html,

                "html",

                "utf-8"

            )

        )


        servidor.sendmail(

            remitente,

            destino.strip(),

            msg.as_string()

        )


        log(
            f"Enviado a {destino}"
        )



    servidor.quit()



# ======================================================
# MAIN
# ======================================================

def main():


    log(
        "INICIANDO MONITOR SECOP"
    )


    procesos = obtener_procesos()


    contratos = obtener_contratos()



    html = generar_html(

        procesos,

        contratos

    )



    guardar(html)



    enviar_email(
        html
    )



    log(
        "FINALIZADO"
    )



if __name__ == "__main__":

    main()
