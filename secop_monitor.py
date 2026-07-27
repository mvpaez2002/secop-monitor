import os
import smtplib
import requests
import html

from datetime import datetime
from pathlib import Path

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


# ======================================================
# CONFIGURACION
# ======================================================

API_SECOP = "https://www.datos.gov.co/resource/p6dx-8zbt.json"

LIMITE = 5000


PALABRAS = [

    "ciberseguridad",
    "seguridad informatica",
    "seguridad informática",
    "seguridad de la información",

    "firewall",
    "fortinet",
    "checkpoint",
    "palo alto",

    "soc",
    "siem",

    "monitoreo",
    "centro de control",
    "centro operaciones",

    "data center",
    "centro de datos",

    "servidores",
    "storage",

    "cloud",
    "nube",
    "azure",
    "aws",

    "biometria",
    "biometría",
    "facial",
    "reconocimiento",

    "abis",
    "verilook",
    "neurotechnology",

    "firma digital",
    "certificado digital",

    "software",
    "hardware",

    "redes",
    "switch",
    "router",

    "cctv",
    "videovigilancia",
    "camaras",
    "cámaras"

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
# CONSULTAR API
# ======================================================

def consultar_secop():

    try:

        log("Consultando SECOP...")


        respuesta = requests.get(

            API_SECOP,

            params={

                "$limit": LIMITE,

                "$order":
                "fecha_de_publicacion_del DESC"

            },

            timeout=300

        )


        respuesta.raise_for_status()


        datos = respuesta.json()


        log(
            f"SECOP devolvio {len(datos)} registros"
        )


        if datos:

            log(
                "Primer registro: "
                +
                str(
                    datos[0].get(
                        "entidad",
                        ""
                    )
                )
            )


        return datos


    except Exception as e:

        log(
            "ERROR API: "
            +
            str(e)
        )

        return []



# ======================================================
# BUSCAR OPORTUNIDADES
# ======================================================

def analizar(datos):


    resultados=[]


    for item in datos:


        texto = " ".join([

            str(
                item.get(
                    "nombre_del_procedimiento",
                    ""
                )
            ),


            str(
                item.get(
                    "descripci_n_del_procedimiento",
                    ""
                )
            ),


            str(
                item.get(
                    "codigo_principal_de_categoria",
                    ""
                )
            ),


            str(
                item.get(
                    "categorias_adicionales",
                    ""
                )
            ),


            str(
                item.get(
                    "nombre_del_proveedor",
                    ""
                )
            )

        ]).lower()



        encontrados=[]


        for palabra in PALABRAS:

            if palabra.lower() in texto:

                encontrados.append(
                    palabra
                )



        # No eliminamos nada todavía
        # solo marcamos coincidencias

        item["coincidencias"] = ", ".join(
            encontrados
        )


        item["nivel"] = len(
            encontrados
        )


        resultados.append(
            item
        )


    resultados.sort(

        key=lambda x:x["nivel"],

        reverse=True

    )


    return resultados



# ======================================================
# GENERAR HTML
# ======================================================

def generar_html(datos):


    filas=""


    for r in datos[:100]:


        url = ""


        if isinstance(
            r.get("urlproceso"),
            dict
        ):

            url = r["urlproceso"].get(
                "url",
                ""
            )



        filas += f"""

<tr>

<td>
{html.escape(str(r.get('entidad','')))}
</td>


<td>
{html.escape(str(r.get('nombre_del_procedimiento','')))}
</td>


<td>

{html.escape(
str(r.get('descripci_n_del_procedimiento',''))[:250]
)}

</td>


<td>

{r.get('codigo_principal_de_categoria','')}

</td>


<td>

Nivel:
{r.get('nivel',0)}

<br>

{r.get('coincidencias','')}

</td>


<td>

<a href="{url}">
Abrir SECOP
</a>

</td>


</tr>

"""



    if not filas:


        filas="""

<tr>

<td colspan="6">

Sin datos

</td>

</tr>

"""



    return f"""

<html>

<head>

<meta charset="utf-8">

<style>

body{{font-family:Arial;background:#eee;padding:20px}}

table{{width:100%;background:white;border-collapse:collapse}}

th{{background:#003566;color:white;padding:10px}}

td{{padding:8px;border-bottom:1px solid #ddd;font-size:12px}}

</style>

</head>


<body>


<h1>
Monitor SECOP Tecnología
</h1>


<p>
Fecha:
{datetime.now()}
</p>


<p>
Registros analizados:
{len(datos)}
</p>


<table>


<tr>

<th>
Entidad
</th>

<th>
Proceso
</th>

<th>
Descripción
</th>

<th>
Código
</th>

<th>
Coincidencias
</th>

<th>
Link
</th>

</tr>


{filas}


</table>


</body>

</html>

"""



# ======================================================
# GUARDAR
# ======================================================

def guardar(html_text):


    Path(
        "informe_secop.html"
    ).write_text(

        html_text,

        encoding="utf-8"

    )


    log(
        "HTML creado"
    )



# ======================================================
# ENVIAR EMAIL
# ======================================================

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


        mensaje=MIMEMultipart(
            "alternative"
        )


        mensaje["Subject"] = (
            "Informe SECOP Tecnologia"
        )


        mensaje["From"]=usuario


        mensaje["To"]=correo.strip()



        mensaje.attach(

            MIMEText(

                html_text,

                "html",

                "utf-8"

            )

        )


        servidor.sendmail(

            usuario,

            correo.strip(),

            mensaje.as_string()

        )


        log(
            "Enviado a "
            +
            correo
        )


    servidor.quit()



# ======================================================
# MAIN
# ======================================================

def main():


    log("====================")

    log(
        "INICIO MONITOR SECOP"
    )

    log("====================")



    datos = consultar_secop()



    if not datos:

        log(
            "NO LLEGARON DATOS"
        )

        return



    resultados = analizar(
        datos
    )



    log(

        "Resultados analizados: "
        +
        str(len(resultados))

    )



    informe = generar_html(
        resultados
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



if __name__ == "__main__":

    main()
