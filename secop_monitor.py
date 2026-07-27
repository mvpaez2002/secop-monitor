import os
import smtplib
import requests
import html

from datetime import datetime, timedelta
from pathlib import Path

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


# ==========================================================
# CONFIGURACIÓN
# ==========================================================

API_SECOP = "https://www.datos.gov.co/resource/p6dx-8zbt.json"

DIAS_BUSQUEDA = 120

MAX_RESULTADOS_API = 500

MAX_INFORME = 100



# ==========================================================
# PALABRAS DE INTERÉS
# ==========================================================

PALABRAS_CLAVE = [

    "ciberseguridad",
    "seguridad informática",
    "seguridad informatica",
    "seguridad de la información",
    "seguridad de la informacion",

    "firewall",
    "fortinet",
    "checkpoint",
    "palo alto",

    "soc",
    "siem",

    "monitoreo",
    "centro de control",
    "centro de operaciones",

    "cctv",
    "videovigilancia",

    "biometria",
    "biometría",
    "huella",
    "facial",
    "reconocimiento",

    "abis",
    "verilook",
    "neurotechnology",

    "data center",
    "centro de datos",

    "servidores",
    "storage",
    "almacenamiento",

    "cloud",
    "nube",
    "aws",
    "azure",

    "virtualizacion",
    "virtualización",

    "backup",
    "respaldo",

    "redes",
    "switch",
    "router",

    "software",

    "certificado digital",
    "firma digital",

    "inteligencia artificial",
    "analitica",
    "analítica"

]


# ==========================================================
# UNSPSC TECNOLOGÍA
# ==========================================================

CODIGOS_UNSPSC = {

    "4323": "Software",

    "432332": "Software de seguridad",

    "4322": "Redes y comunicaciones",

    "4321": "Hardware",

    "4320": "Tecnología informática",

    "8111": "Servicios TI",

    "4617": "Seguridad electrónica",

    "4618": "Control de acceso"

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
# CONSULTA API SECOP
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
        "software",
        "digital",
        "tecnologia",
        "sistema",
        "redes",
        "datos",
        "biometria",
        "cloud",
        "servidores"

    ]


    todos = []


    for palabra in consultas:

        log(
            f"Consultando {palabra}"
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

                timeout=60

            )


            respuesta.raise_for_status()


            datos = respuesta.json()


            log(
                f"{palabra}: {len(datos)} registros"
            )


            todos.extend(datos)


        except Exception as error:

            log(
                f"Error {palabra}: {error}"
            )


    return eliminar_duplicados(todos)



# ==========================================================
# ELIMINAR REPETIDOS
# ==========================================================

def eliminar_duplicados(datos):

    vistos = set()

    resultado = []


    for item in datos:

        identificador = (

            item.get(
                "id_del_proceso",
                ""
            )

        )


        if identificador not in vistos:

            vistos.add(
                identificador
            )

            resultado.append(
                item
            )


    return resultado



# ==========================================================
# CALCULAR RELEVANCIA
# ==========================================================

def analizar_registro(registro):

    texto = " ".join([

        str(
            registro.get(
                "nombre_del_procedimiento",
                ""
            )
        ),

        str(
            registro.get(
                "descripci_n_del_procedimiento",
                ""
            )
        ),

        str(
            registro.get(
                "codigo_principal_de_categoria",
                ""
            )
        ),

        str(
            registro.get(
                "categorias_adicionales",
                ""
            )
        ),

        str(
            registro.get(
                "nombre_del_proveedor",
                ""
            )
        )

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

    ).lower()



    for clave, descripcion in CODIGOS_UNSPSC.items():


        if clave in codigo:


            puntos += 20

            motivos.append(
                descripcion
            )



    return puntos, list(set(motivos))



# ==========================================================
# FILTRAR OPORTUNIDADES
# ==========================================================

def filtrar(datos):

    encontrados = []


    for registro in datos:


        puntos, motivos = analizar_registro(
            registro
        )


        if puntos >= 20:


            registro["puntaje"] = puntos

            registro["motivos"] = (
                ", ".join(motivos)
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

        return (
            "$ {:,.0f}".format(numero)
        )

    except:

        return "-"



# ==========================================================
# CREAR HTML
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


        filas += f"""

<tr>

<td>{html.escape(str(entidad))}</td>

<td>{html.escape(str(descripcion)[:250])}</td>

<td>{dinero(valor)}</td>

<td>{r.get('codigo_principal_de_categoria','')}</td>

<td>
{r.get('puntaje')} %
<br>
{r.get('motivos')}
</td>

<td>

<a href="{r.get('urlproceso',{}).get('url','')}">

Ver proceso

</a>

</td>

</tr>

"""


    if not filas:

        filas = """

<tr>

<td colspan="6">

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

background:#f1f5f9;

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

font-size:12px;

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


<p>
Resultados:
{len(datos)}
</p>


<table>


<tr>

<th>Entidad</th>

<th>Descripción</th>

<th>Valor</th>

<th>UNSPSC</th>

<th>Detectado</th>

<th>Link</th>

</tr>


{filas}


</table>


</body>

</html>

"""



# ==========================================================
# GUARDAR HTML
# ==========================================================

def guardar(html_text):


    nombre = (

        "Informe_SECOP_"

        +

        datetime.now().strftime(
            "%Y%m%d_%H%M"
        )

        +

        ".html"

    )


    Path(nombre).write_text(

        html_text,

        encoding="utf-8"

    )


    log(
        f"Archivo creado {nombre}"
    )



# ==========================================================
# ENVIAR CORREO
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
            "Faltan secretos Gmail"
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



    for correo in destinatarios.split(","):


        mensaje = MIMEMultipart(
            "alternative"
        )


        mensaje["Subject"] = (

            "🛡️ Informe SECOP Tecnología"

        )


        mensaje["From"] = remitente

        mensaje["To"] = correo.strip()



        mensaje.attach(

            MIMEText(

                html_text,

                "html",

                "utf-8"

            )

        )


        servidor.sendmail(

            remitente,

            correo.strip(),

            mensaje.as_string()

        )


        log(
            f"Enviado {correo}"
        )



    servidor.quit()



# ==========================================================
# EJECUCIÓN
# ==========================================================

def main():

    log(
        "INICIANDO MONITOR SECOP"
    )


    datos = consultar_secop()


    log(
        f"Total recibidos: {len(datos)}"
    )


    oportunidades = filtrar(datos)


    log(
        f"Oportunidades detectadas: {len(oportunidades)}"
    )


    informe = generar_html(
        oportunidades
    )


    guardar(
        informe
    )


    enviar_correo(
        informe
    )


    log(
        "FINALIZADO"
    )



if __name__ == "__main__":

    main()
