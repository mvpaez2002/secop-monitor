import os
import smtplib
import requests
import html

from datetime import datetime, timedelta
from pathlib import Path

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


# =====================================================
# CONFIGURACION
# =====================================================

API = "https://www.datos.gov.co/resource/p6dx-8zbt.json"

DIAS = 180

LIMITE_API = 50000

LIMITE_INFORME = 100



# =====================================================
# PALABRAS OBJETIVO
# =====================================================

KEYWORDS = [

    "ciberseguridad",
    "seguridad informática",
    "seguridad informatica",
    "seguridad de la información",

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
    "video vigilancia",
    "videovigilancia",

    "biometria",
    "biometría",
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
    "azure",
    "aws",

    "virtualizacion",
    "virtualización",

    "backup",

    "redes",
    "switch",
    "router",

    "software",

    "firma digital",
    "certificado digital"

]



# =====================================================
# CODIGOS UNSPSC
# =====================================================

UNSPSC = {

    "4323": "Software",

    "432332": "Software seguridad",

    "4322": "Redes",

    "4321": "Hardware",

    "4320": "Tecnología",

    "8111": "Servicios TI",

    "4617": "Seguridad electrónica",

    "4618": "Control acceso"

}



# =====================================================
# LOG
# =====================================================

def log(msg):

    print(
        f"[{datetime.now().strftime('%H:%M:%S')}] {msg}",
        flush=True
    )



# =====================================================
# DESCARGAR SECOP
# =====================================================

def descargar_secop():


    fecha = (

        datetime.now()
        -
        timedelta(days=DIAS)

    ).strftime(

        "%Y-%m-%dT00:00:00.000"

    )


    try:


        log(
            "Consultando SECOP..."
        )


        r = requests.get(

            API,

            params={

                "$limit": LIMITE_API,

                "$order":
                "fecha_de_publicacion_del DESC"

            },

            timeout=120

        )


        r.raise_for_status()


        datos = r.json()


        log(

            f"SECOP devolvió {len(datos)} registros"

        )


        return datos



    except Exception as e:


        log(
            f"ERROR API {e}"
        )


        return []



# =====================================================
# ANALISIS INTELIGENTE
# =====================================================

def analizar(registro):


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



    for palabra in KEYWORDS:


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



    for c,nombre in UNSPSC.items():


        if c in codigo:


            puntos += 25

            motivos.append(
                nombre
            )



    return puntos, list(set(motivos))



# =====================================================
# FILTRAR
# =====================================================

def filtrar(datos):


    salida=[]


    vistos=set()



    for r in datos:


        puntos,motivos = analizar(r)



        if puntos >= 20:


            idp = r.get(
                "id_del_proceso",
                ""
            )


            if idp not in vistos:


                vistos.add(idp)


                r["puntaje"]=puntos

                r["motivos"]=" | ".join(motivos)


                salida.append(r)



    salida.sort(

        key=lambda x:x["puntaje"],

        reverse=True

    )


    return salida



# =====================================================
# HTML
# =====================================================

def generar_html(datos):


    filas=""


    for r in datos[:LIMITE_INFORME]:


        filas += f"""

<tr>

<td>{html.escape(str(r.get('entidad','-')))}</td>


<td>

{html.escape(str(r.get('descripci_n_del_procedimiento','-'))[:250])}

</td>


<td>

{r.get('codigo_principal_de_categoria','')}

</td>


<td>

{r.get('puntaje')}

<br>

{r.get('motivos')}

</td>


<td>

<a href="{r.get('urlproceso',{}).get('url','')}">

Abrir

</a>

</td>


</tr>

"""



    if not filas:


        filas="""

<tr>

<td colspan="5">

SIN RESULTADOS

</td>

</tr>

"""



    return f"""

<html>

<head>

<meta charset="utf-8">

<style>

body{{font-family:Arial;background:#f2f2f2;padding:20px}}

table{{width:100%;background:white;border-collapse:collapse}}

th{{background:#003566;color:white;padding:10px}}

td{{padding:8px;border-bottom:1px solid #ddd;font-size:12px}}

</style>

</head>


<body>


<h1>🛡️ Monitor SECOP Tecnología</h1>


<p>

Generado:

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

<th>UNSPSC</th>

<th>Detectado</th>

<th>Link</th>

</tr>


{filas}


</table>


</body>

</html>

"""



# =====================================================
# GUARDAR
# =====================================================

def guardar(texto):


    nombre="informe_secop.html"


    Path(nombre).write_text(

        texto,

        encoding="utf-8"

    )


    log(
        "HTML generado"
    )



# =====================================================
# EMAIL
# =====================================================

def enviar(html_text):


    usuario=os.getenv(
        "GMAIL_REMITENTE"
    )


    clave=os.getenv(
        "GMAIL_PASSWORD"
    )


    destinos=os.getenv(
        "DESTINATARIOS"
    )


    if not usuario or not clave or not destinos:


        log(
            "Correo no configurado"
        )

        return



    servidor=smtplib.SMTP_SSL(

        "smtp.gmail.com",

        465

    )


    servidor.login(

        usuario,

        clave

    )



    for correo in destinos.split(","):


        msg=MIMEMultipart(
            "alternative"
        )


        msg["Subject"]="🛡️ Monitor SECOP Tecnología"


        msg["From"]=usuario


        msg["To"]=correo.strip()



        msg.attach(

            MIMEText(

                html_text,

                "html",

                "utf-8"

            )

        )


        servidor.sendmail(

            usuario,

            correo.strip(),

            msg.as_string()

        )


        log(
            f"Enviado {correo}"
        )


    servidor.quit()



# =====================================================
# MAIN
# =====================================================

def main():


    log(
        "INICIANDO"
    )


    datos=descargar_secop()


    oportunidades=filtrar(datos)


    log(

        f"Oportunidades encontradas: {len(oportunidades)}"

    )


    informe=generar_html(
        oportunidades
    )


    guardar(
        informe
    )


    enviar(
        informe
    )


    log(
        "FINALIZADO"
    )



if __name__=="__main__":

    main()
