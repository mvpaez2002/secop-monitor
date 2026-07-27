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
# CÓDIGOS UNSPSC TECNOLOGÍA
# ======================================================

CODIGOS_TECNOLOGIA = {

    "81111800": "Servicios seguridad TI",
    "81111801": "Ciberseguridad",

    "43222500": "Seguridad de red",
    "43222600": "Equipos de red",

    "43230000": "Software",
    "43231500": "Software gestión",
    "43232200": "Software seguridad",

    "43211500": "Computadores",
    "43201800": "Almacenamiento",

    "81112000": "Procesamiento datos",
    "81112100": "Servicios internet",

    "46171600": "Seguridad y vigilancia",
    "46171619": "Sistemas vigilancia"

}



# ======================================================
# LOG
# ======================================================

def log(texto):

    print(
        f"[{datetime.now().strftime('%H:%M:%S')}] {texto}",
        flush=True
    )



# ======================================================
# CONSULTAR SECOP
# ======================================================

def consultar_api(url):

    try:

        r = requests.get(
            url,
            params={
                "$limit": LIMITE_API
            },
            headers=HEADERS,
            timeout=90
        )

        r.raise_for_status()

        datos = r.json()

        log(
            f"Registros recibidos: {len(datos)}"
        )


        if datos:

            log("Campos detectados:")

            print(datos[0].keys())


        return datos


    except Exception as e:

        log(
            f"Error API: {e}"
        )

        return []



# ======================================================
# EXTRAER TEXTO DEL REGISTRO
# ======================================================

def texto_registro(registro):

    texto = ""

    for campo, valor in registro.items():

        if valor:

            texto += " " + str(valor)


    return texto



# ======================================================
# BUSCAR UNSPSC
# ======================================================

def analizar_unspsc(registro):

    texto = texto_registro(
        registro
    )


    encontrados = []


    for codigo, nombre in CODIGOS_TECNOLOGIA.items():


        if codigo in texto:


            encontrados.append(
                f"{codigo} - {nombre}"
            )


    return encontrados



# ======================================================
# FILTRAR TECNOLOGÍA
# ======================================================

def filtrar_tecnologia(registros):

    resultado = []


    for registro in registros:


        codigos = analizar_unspsc(
            registro
        )


        if codigos:


            registro["categoria_tecnologia"] = (
                ", ".join(codigos)
            )


            resultado.append(
                registro
            )


    return resultado



# ======================================================
# OBTENER DATOS
# ======================================================

def obtener_procesos():

    log(
        "Consultando procesos SECOP..."
    )


    datos = consultar_api(
        API_PROCESOS
    )


    encontrados = filtrar_tecnologia(
        datos
    )


    log(
        f"Procesos tecnología: {len(encontrados)}"
    )


    return encontrados



def obtener_contratos():

    log(
        "Consultando contratos SECOP..."
    )


    datos = consultar_api(
        API_CONTRATOS
    )


    encontrados = filtrar_tecnologia(
        datos
    )


    log(
        f"Contratos tecnología: {len(encontrados)}"
    )


    return encontrados



# ======================================================
# FORMATO DINERO
# ======================================================

def dinero(valor):

    try:

        numero = float(valor)

        return f"${numero:,.0f}"

    except:

        return "-"



# ======================================================
# GENERAR HTML
# ======================================================

def generar_html(procesos, contratos):


    def fila(registro):


        entidad = (
            registro.get("nombre_entidad")
            or
            registro.get("entidad")
            or
            "-"
        )


        descripcion = (

            registro.get("objeto_del_contrato")

            or

            registro.get("descripcion_del_proceso")

            or

            registro.get(
                "descripci_n_del_procedimiento"
            )

            or

            "-"

        )


        valor = (

            registro.get("valor_del_contrato")

            or

            registro.get("precio_base")

            or

            0

        )


        return f"""

<tr>

<td>{entidad}</td>

<td>{str(descripcion)[:200]}</td>

<td>{dinero(valor)}</td>

<td>
{registro.get('categoria_tecnologia','')}
</td>

</tr>

"""


    filas = ""


    for r in (contratos + procesos)[:LIMITE_INFORME]:

        filas += fila(r)



    if not filas:

        filas = """

<tr>

<td colspan="4">
No se encontraron códigos tecnológicos
</td>

</tr>

"""



    return f"""

<html>

<head>

<meta charset="utf-8">

<style>

body{{font-family:Arial;background:#f2f5f9;padding:20px}}

table{{width:100%;border-collapse:collapse;background:white}}

th{{background:#003566;color:white;padding:10px}}

td{{padding:10px;border-bottom:1px solid #ddd}}

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

<th>Código UNSPSC</th>

</tr>


{filas}


</table>


</body>

</html>

"""



# ======================================================
# GUARDAR HTML
# ======================================================

def guardar(html):

    archivo = (

        "informe_secop_"

        +

        datetime.now().strftime(
            "%Y%m%d_%H%M"
        )

        +

        ".html"

    )


    Path(archivo).write_text(
        html,
        encoding="utf-8"
    )


    log(
        f"Archivo creado: {archivo}"
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



    lista = [
        x.strip()
        for x in destinos.split(",")
        if x.strip()
    ]



    servidor = smtplib.SMTP_SSL(
        "smtp.gmail.com",
        465
    )


    servidor.login(
        remitente,
        password
    )



    for destino in lista:


        msg = MIMEMultipart(
            "alternative"
        )


        msg["Subject"] = (
            "Monitor SECOP Tecnología"
        )


        msg["From"] = remitente

        msg["To"] = destino



        msg.attach(
            MIMEText(
                html,
                "html",
                "utf-8"
            )
        )


        servidor.sendmail(
            remitente,
            destino,
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


    enviar_email(html)



    log(
        "FINALIZADO"
    )



if __name__ == "__main__":

    main()
