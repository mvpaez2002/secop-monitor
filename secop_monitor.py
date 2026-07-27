"""
SECOP II Monitor Tecnología - Versión Diagnóstico
=================================================

Descarga datos de SECOP II y analiza oportunidades:

- Ciberseguridad
- SOC
- SIEM
- ABIS
- VeriLook
- Neurotechnology
- Biometría
- Reconocimiento facial
- Data Center
- Cloud
- AWS
- Azure
- IA
- Analítica
- Centro de monitoreo
- CCTV
- Infraestructura TI

Modo:
API SECOP -> Python -> Analizador -> HTML -> Gmail
"""


import os
import sys
import smtplib
import requests


from datetime import datetime

from pathlib import Path


from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText



# ======================================================
# CONFIGURACIÓN
# ======================================================


CONFIG = {

    "limite_api": 5000,

    "limite_informe": 100

}




# ======================================================
# PALABRAS DE INTERÉS
# ======================================================


PALABRAS_ALTA = [

    "ciberseguridad",

    "seguridad informática",

    "seguridad informatica",

    "soc",

    "siem",

    "centro de operaciones de seguridad",

    "abis",

    "mega matcher",

    "verilook",

    "neurotechnology",

    "reconocimiento facial",

    "biometría",

    "biometria",

    "identificación biométrica",

    "identificacion biometrica",

    "control de acceso"

]



PALABRAS_MEDIA = [

    "data center",

    "centro de datos",

    "servidores",

    "almacenamiento",

    "cloud",

    "nube",

    "aws",

    "azure",

    "google cloud",

    "virtualización",

    "virtualizacion",

    "redes",

    "telecomunicaciones",

    "infraestructura tecnológica",

    "infraestructura ti"

]



PALABRAS_GENERAL = [

    "software",

    "hardware",

    "tecnología",

    "tecnologia",

    "inteligencia artificial",

    "ia",

    "analítica",

    "analitica",

    "big data",

    "monitoreo",

    "centro de control",

    "videovigilancia",

    "cctv",

    "plataforma digital"

]





# ======================================================
# APIS
# ======================================================


API_CONTRATOS = (

"https://www.datos.gov.co/resource/jbjy-vk9h.json"

)


API_PROCESOS = (

"https://www.datos.gov.co/resource/p6dx-8zbt.json"

)



HEADERS = {

    "Accept":"application/json"

}





# ======================================================
# LOG
# ======================================================


def log(texto):

    hora = datetime.now().strftime("%H:%M:%S")

    print(
        f"[{hora}] {texto}",
        flush=True
    )





# ======================================================
# CONSULTA DIRECTA SECOP
# ======================================================


def consultar_secop(url):


    try:


        respuesta = requests.get(

            url,

            params={

                "$limit":
                CONFIG["limite_api"]

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
                "===== CAMPOS DETECTADOS ====="
            )


            print(
                datos[0].keys()
            )


            log(
                "===== PRIMER REGISTRO ====="
            )


            print(
                datos[0]
            )



        return datos



    except Exception as e:


        log(
            f"Error consultando API: {e}"
        )


        return []
# ======================================================
# EXTRAER TEXTO COMPLETO DEL REGISTRO
# ======================================================


def obtener_texto_registro(registro):


    textos = []


    for clave, valor in registro.items():


        if valor is not None:


            textos.append(

                str(valor)

            )



    return (

        " ".join(textos)

        .lower()

    )





# ======================================================
# ANALIZADOR DE OPORTUNIDADES
# ======================================================


def analizar_registro(registro):


    texto = obtener_texto_registro(

        registro

    )



    resultado = {


        "nivel":

            "🟢 Normal",


        "coincidencias":

            []

    }



    # Alta prioridad

    for palabra in PALABRAS_ALTA:


        if palabra.lower() in texto:


            resultado["nivel"] = (

                "🔴 Alta"

            )


            resultado["coincidencias"].append(

                palabra

            )




    # Media prioridad

    if resultado["nivel"] != "🔴 Alta":


        for palabra in PALABRAS_MEDIA:


            if palabra.lower() in texto:


                resultado["nivel"] = (

                    "🟠 Media"

                )


                resultado["coincidencias"].append(

                    palabra

                )




    # Tecnología general

    for palabra in PALABRAS_GENERAL:


        if palabra.lower() in texto:


            resultado["coincidencias"].append(

                palabra

            )



    return resultado





# ======================================================
# FILTRO TECNOLÓGICO
# ======================================================


def filtrar_tecnologia(registros):


    encontrados = []



    for registro in registros:


        analisis = analizar_registro(

            registro

        )



        if analisis["coincidencias"]:



            registro["prioridad"] = (

                analisis["nivel"]

            )



            registro["palabras_detectadas"] = (

                ", ".join(

                    analisis["coincidencias"]

                )

            )



            encontrados.append(

                registro

            )



    return encontrados





# ======================================================
# OBTENER CONTRATOS
# ======================================================


def obtener_contratos():


    log(

        "Consultando contratos SECOP..."

    )


    registros = consultar_secop(

        API_CONTRATOS

    )



    encontrados = filtrar_tecnologia(

        registros

    )



    log(

        f"Contratos tecnológicos encontrados: {len(encontrados)}"

    )



    return encontrados





# ======================================================
# OBTENER PROCESOS
# ======================================================


def obtener_procesos():


    log(

        "Consultando procesos SECOP..."

    )


    registros = consultar_secop(

        API_PROCESOS

    )



    encontrados = filtrar_tecnologia(

        registros

    )



    log(

        f"Procesos tecnológicos encontrados: {len(encontrados)}"

    )



    return encontrados
    # ======================================================
# UTILIDADES HTML
# ======================================================


def dinero(valor):

    try:

        numero = float(valor or 0)


        if numero >= 1000000000:

            return (
                f"${numero/1000000000:.1f} B"
            )


        if numero >= 1000000:

            return (
                f"${numero/1000000:.0f} M"
            )


        return f"${numero:,.0f}"


    except:

        return "N/D"





def obtener_campo(registro, campos):


    for campo in campos:


        if campo in registro:


            return registro[campo]


    return "-"





# ======================================================
# CREAR FILAS HTML
# ======================================================


def crear_fila(registro):


    entidad = obtener_campo(

        registro,

        [

            "nombre_entidad",

            "entidad",

            "nombre_de_la_entidad"

        ]

    )



    descripcion = obtener_campo(

        registro,

        [

            "objeto_del_contrato",

            "descripcion_del_proceso",

            "descripci_n_del_procedimiento",

            "objeto"

        ]

    )



    valor = obtener_campo(

        registro,

        [

            "valor_del_contrato",

            "precio_base",

            "valor_estimado"

        ]

    )



    fecha = obtener_campo(

        registro,

        [

            "fecha_de_firma",

            "fecha_de_publicacion_del",

            "fecha_de_publicacion"

        ]

    )



    return f"""

<tr>

<td>

{registro.get('prioridad','')}

</td>


<td>

{entidad}

</td>


<td>

{str(descripcion)[:180]}

</td>


<td>

{dinero(valor)}

</td>


<td>

{registro.get(
'palabras_detectadas',
''
)}

</td>


<td>

{str(fecha)[:10]}

</td>


</tr>

"""





# ======================================================
# GENERADOR HTML PRINCIPAL
# ======================================================


def generar_html(contratos, procesos):


    filas_contratos = ""


    for registro in contratos[

        :CONFIG["limite_informe"]

    ]:


        filas_contratos += crear_fila(

            registro

        )




    filas_procesos = ""


    for registro in procesos[

        :CONFIG["limite_informe"]

    ]:


        filas_procesos += crear_fila(

            registro

        )





    if not filas_contratos:


        filas_contratos = """

<tr>

<td colspan="6">

No se encontraron contratos tecnológicos

</td>

</tr>

"""



    if not filas_procesos:


        filas_procesos = """

<tr>

<td colspan="6">

No se encontraron procesos tecnológicos

</td>

</tr>

"""




    html = f"""

<!DOCTYPE html>

<html lang="es">


<head>

<meta charset="utf-8">


<title>

Monitor SECOP Tecnología

</title>


<style>


body {{

font-family:Arial, sans-serif;

background:#eef2f7;

padding:20px;

}}



.container {{

max-width:1200px;

margin:auto;

background:white;

padding:30px;

border-radius:15px;

}}



.header {{

background:#003566;

color:white;

padding:25px;

border-radius:10px;

}}



table {{

width:100%;

border-collapse:collapse;

margin-top:20px;

font-size:13px;

}}



th {{

background:#003566;

color:white;

padding:10px;

}}



td {{

padding:9px;

border-bottom:1px solid #ddd;

}}



tr:nth-child(even) {{

background:#f7f9fc;

}}



.badge {{

font-weight:bold;

}}


</style>


</head>


<body>


<div class="container">


<div class="header">


<h1>

🛡️ Monitor SECOP II Tecnología

</h1>


<p>

Generado:

{datetime.now().strftime("%d/%m/%Y %H:%M")}

</p>


</div>



<h2>

🔐 Contratos detectados

</h2>


<table>


<tr>

<th>

Prioridad

</th>


<th>

Entidad

</th>


<th>

Descripción

</th>


<th>

Valor

</th>


<th>

Coincidencias

</th>


<th>

Fecha

</th>

</tr>


{filas_contratos}


</table>





<h2>

🚀 Nuevas oportunidades

</h2>


<table>


<tr>

<th>

Prioridad

</th>


<th>

Entidad

</th>


<th>

Descripción

</th>


<th>

Presupuesto

</th>


<th>

Coincidencias

</th>


<th>

Fecha

</th>

</tr>


{filas_procesos}


</table>



<p>

Fuente: SECOP II - datos.gov.co

</p>



</div>


</body>


</html>

"""



    return html
    # ======================================================
# GUARDAR HTML
# ======================================================


def guardar_html(html):


    nombre = (

        "monitor_secop_tecnologia_"

        +

        datetime.now().strftime(

            "%Y-%m-%d_%H-%M"

        )

        +

        ".html"

    )


    Path(nombre).write_text(

        html,

        encoding="utf-8"

    )


    log(

        f"HTML creado: {nombre}"

    )


    return nombre





# ======================================================
# ENVÍO EMAIL GMAIL
# ======================================================


def enviar_correo(html, contratos, procesos):


    remitente = os.environ.get(

        "GMAIL_REMITENTE",

        ""

    )


    password = os.environ.get(

        "GMAIL_PASSWORD",

        ""

    )


    destinatarios = os.environ.get(

        "DESTINATARIOS",

        ""

    )



    if not remitente or not password:


        log(

            "⚠️ Gmail no configurado"

        )


        return




    lista = [

        correo.strip()

        for correo in destinatarios.split(",")

        if correo.strip()

    ]



    if not lista:


        log(

            "⚠️ No hay destinatarios"

        )


        return




    asunto = (

        "🛡️ Monitor SECOP Tecnología "

        +

        datetime.now().strftime(

            "%d/%m/%Y"

        )

        +

        f" | {len(contratos)} contratos"

        +

        f" | {len(procesos)} oportunidades"

    )




    try:


        servidor = smtplib.SMTP_SSL(

            "smtp.gmail.com",

            465

        )


        servidor.login(

            remitente,

            password

        )




        for destino in lista:


            mensaje = MIMEMultipart(

                "alternative"

            )


            mensaje["Subject"] = asunto


            mensaje["From"] = (

                "Monitor SECOP <"

                +

                remitente

                +

                ">"

            )


            mensaje["To"] = destino




            mensaje.attach(

                MIMEText(

                    html,

                    "html",

                    "utf-8"

                )

            )



            servidor.sendmail(

                remitente,

                destino,

                mensaje.as_string()

            )



            log(

                f"Correo enviado a: {destino}"

            )




        servidor.quit()



    except Exception as error:


        log(

            f"Error enviando correo: {error}"

        )





# ======================================================
# EJECUCIÓN PRINCIPAL
# ======================================================


def main():


    log(

        "=" * 60

    )


    log(

        "🛡️ INICIANDO MONITOR SECOP TECNOLOGÍA"

    )


    log(

        "=" * 60

    )



    contratos = obtener_contratos()



    procesos = obtener_procesos()




    log(

        "Creando informe HTML..."

    )



    html = generar_html(

        contratos,

        procesos

    )




    guardar_html(

        html

    )




    log(

        "Preparando envío..."

    )



    enviar_correo(

        html,

        contratos,

        procesos

    )




    log(

        "RESUMEN FINAL"

    )


    log(

        f"Contratos encontrados: {len(contratos)}"

    )


    log(

        f"Procesos encontrados: {len(procesos)}"

    )



    log(

        "✅ TERMINADO"

    )





if __name__ == "__main__":


    main()
