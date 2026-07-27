"""
SECOP II Monitor Inteligente
============================

Monitor automático de oportunidades tecnológicas
en SECOP II.

Busca:
- Ciberseguridad
- SOC
- Centros de control
- Monitoreo
- Data Center
- Nube / Cloud
- Biometría
- ABIS
- IA
- Analítica
- Infraestructura TI
- Redes
- Software

Compatible con GitHub Actions.
"""


import os
import sys
import smtplib
import requests


from datetime import datetime, timedelta
from pathlib import Path


from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText



# ======================================================
# CONFIGURACIÓN PRINCIPAL
# ======================================================


CONFIG = {


    # Colombia completa
    "departamento": "",


    # Cantidad de días a revisar

    "dias_contratos": 30,

    "dias_procesos": 60,


    # Máximo de resultados

    "limite": 100,


    # Palabras de búsqueda tecnológica

    "palabras_clave": [
       "software"
    ]

}



# ======================================================
# API SECOP II
# ======================================================


API_CONTRATOS = (

    "https://www.datos.gov.co/resource/jbjy-vk9h.json"

)


API_PROCESOS = (

    "https://www.datos.gov.co/resource/p6dx-8zbt.json"

)



HEADERS = {

    "Accept": "application/json"

}




# ======================================================
# UTILIDADES
# ======================================================


def log(mensaje):

    hora = datetime.now().strftime("%H:%M:%S")

    print(
        f"[{hora}] {mensaje}",
        flush=True
    )




def dinero(valor):

    try:

        numero = float(valor)


        if numero >= 1000000000:

            return (
                f"${numero/1000000000:.1f} "
                "mil millones"
            )


        if numero >= 1000000:

            return (
                f"${numero/1000000:.0f} millones"
            )


        return f"${numero:,.0f}"


    except:

        return "N/D"




def fecha(valor):

    if not valor:

        return "-"


    return str(valor)[:10]




# ======================================================
# GENERADOR DE CONDICIÓN DE BÚSQUEDA
# ======================================================


def crear_busqueda(campos):


    condiciones = []


    for palabra in CONFIG["palabras_clave"]:


        filtros = []


        for campo in campos:


            filtros.append(

                f"upper({campo}) like "
                f"upper('%{palabra}%')"

            )


        condiciones.append(

            "("
            +
            " OR ".join(filtros)
            +
            ")"

        )


    return (

        "("
        +
        " OR ".join(condiciones)
        +
        ")"

    )




# ======================================================
# CONSULTA GENERAL API
# ======================================================


def consultar_api(

        url,

        where,

        orden="",

        limite=100

):


    parametros = {


        "$limit": limite

    }



    if where:

        parametros["$where"] = where



    if orden:

        parametros["$order"] = orden




    try:


        respuesta = requests.get(

            url,

            params=parametros,

            headers=HEADERS,

            timeout=40

        )



        log(

            "API: "
            +
            respuesta.url

        )



        respuesta.raise_for_status()



        datos = respuesta.json()



        log(

            f"Datos recibidos: {len(datos)}"

        )



        return datos



    except Exception as error:


        log(

            f"Error API: {error}"

        )


        return []
# ======================================================
# CONSULTA DE CONTRATOS
# ======================================================


def obtener_contratos():


    fecha_inicio = (

        datetime.now()

        -
        timedelta(
            days=CONFIG["dias_contratos"]
        )

    ).strftime("%Y-%m-%dT00:00:00")



    condiciones = [

        f"fecha_de_firma >= '{fecha_inicio}'"

    ]



    # Búsqueda tecnológica en múltiples campos

    busqueda = crear_busqueda(

        [

            "objeto_del_contrato",

            "nombre_entidad",

            "proveedor_adjudicado"

        ]

    )


    condiciones.append(busqueda)



    if CONFIG["departamento"]:


        condiciones.append(

            "upper(departamento) like "

            f"upper('%{CONFIG['departamento']}%')"

        )



    where = " AND ".join(condiciones)



    return consultar_api(

        API_CONTRATOS,

        where,

        "valor_del_contrato DESC",

        CONFIG["limite"]

    )





# ======================================================
# CONSULTA DE PROCESOS / LICITACIONES
# ======================================================


def obtener_procesos():


    fecha_inicio = (

        datetime.now()

        -

        timedelta(
            days=CONFIG["dias_procesos"]
        )

    ).strftime("%Y-%m-%dT00:00:00")



    condiciones = [

        f"fecha_de_publicacion_del >= '{fecha_inicio}'"

    ]



    busqueda = crear_busqueda(

        [

            "descripci_n_del_procedimiento",

            "nombre_entidad",

            "modalidad_de_contratacion"

        ]

    )


    condiciones.append(busqueda)



    if CONFIG["departamento"]:


        condiciones.append(

            "upper(departamento_entidad) like "

            f"upper('%{CONFIG['departamento']}%')"

        )



    where = " AND ".join(condiciones)



    return consultar_api(

        API_PROCESOS,

        where,

        "precio_base DESC",

        CONFIG["limite"]

    )





# ======================================================
# CLASIFICACIÓN DE OPORTUNIDADES
# ======================================================


def clasificar_oportunidad(texto):


    texto = texto.lower()



    palabras_alta = [

        "ciberseguridad",

        "soc",

        "seguridad informática",

        "biometría",

        "abis",

        "reconocimiento facial",

        "centro de operaciones",

        "centro de control"

    ]



    palabras_media = [

        "data center",

        "centro de datos",

        "cloud",

        "nube",

        "servidores",

        "infraestructura",

        "redes"

    ]



    for palabra in palabras_alta:


        if palabra in texto:

            return "🔴 Alta"



    for palabra in palabras_media:


        if palabra in texto:

            return "🟠 Media"



    return "🟢 Normal"





# ======================================================
# PREPARAR DATOS PARA EL INFORME
# ======================================================


def enriquecer_contratos(contratos):


    resultado = []



    for contrato in contratos:


        texto = " ".join([

            str(
                contrato.get(
                    "objeto_del_contrato",
                    ""
                )
            ),


            str(
                contrato.get(
                    "nombre_entidad",
                    ""
                )
            )

        ])



        contrato["prioridad"] = clasificar_oportunidad(texto)



        resultado.append(
            contrato
        )



    return resultado





def enriquecer_procesos(procesos):


    resultado = []



    for proceso in procesos:


        texto = " ".join([

            str(
                proceso.get(
                    "descripci_n_del_procedimiento",
                    ""
                )
            ),


            str(
                proceso.get(
                    "nombre_entidad",
                    ""
                )
            )

        ])



        proceso["prioridad"] = clasificar_oportunidad(texto)



        resultado.append(
            proceso
        )



    return resultado
    # ======================================================
# GENERADOR HTML DEL INFORME
# ======================================================


def generar_html(contratos, procesos):


    fecha_reporte = datetime.now().strftime(
        "%d/%m/%Y %H:%M"
    )


    total_contratos = sum(

        float(
            c.get(
                "valor_del_contrato",
                0
            ) or 0
        )

        for c in contratos

    )


    entidades = len(

        set(

            c.get(
                "nombre_entidad",
                ""
            )

            for c in contratos

        )

    )



    # ------------------------------
    # TABLA CONTRATOS
    # ------------------------------


    filas_contratos = ""



    for c in contratos:


        filas_contratos += f"""

        <tr>


        <td>
        {c.get('prioridad','')}
        </td>


        <td>
        {c.get('nombre_entidad','-')}
        </td>


        <td>
        {c.get('objeto_del_contrato','-')[:130]}
        </td>


        <td>
        {dinero(
            c.get(
                'valor_del_contrato'
            )
        )}
        </td>


        <td>
        {c.get(
            'proveedor_adjudicado',
            '-'
        )}
        </td>


        <td>
        {fecha(
            c.get(
                'fecha_de_firma'
            )
        )}
        </td>


        </tr>

        """



    if not filas_contratos:


        filas_contratos = """

        <tr>

        <td colspan="6">
        No se encontraron contratos
        </td>

        </tr>

        """





    # ------------------------------
    # TABLA PROCESOS
    # ------------------------------


    filas_procesos = ""



    for p in procesos:


        filas_procesos += f"""


        <tr>


        <td>
        {p.get('prioridad','')}
        </td>


        <td>
        {p.get(
            'nombre_entidad',
            '-'
        )}
        </td>


        <td>
        {p.get(
            'descripci_n_del_procedimiento',
            '-'
        )[:130]}
        </td>


        <td>
        {dinero(
            p.get(
                'precio_base'
            )
        )}
        </td>


        <td>
        {fecha(
            p.get(
                'fecha_de_publicacion_del'
            )
        )}
        </td>


        </tr>


        """



    if not filas_procesos:


        filas_procesos = """

        <tr>

        <td colspan="5">
        No se encontraron procesos
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

font-family:
Segoe UI,
Arial,
sans-serif;

background:#eef2f7;

padding:20px;

color:#222;

}}



.container {{

max-width:1200px;

margin:auto;

background:white;

border-radius:15px;

padding:30px;

box-shadow:
0 5px 25px rgba(0,0,0,.12);

}}



.header {{

background:
linear-gradient(
135deg,
#0b3d91,
#0077b6
);

color:white;

padding:25px;

border-radius:12px;

}}



.header h1 {{

margin:0;

}}



.cards {{

display:flex;

gap:15px;

flex-wrap:wrap;

margin:25px 0;

}}



.card {{

background:#edf4ff;

padding:18px;

border-radius:10px;

min-width:180px;

text-align:center;

}}



.card strong {{

font-size:26px;

color:#0b3d91;

}}



table {{

width:100%;

border-collapse:collapse;

margin-top:15px;

font-size:13px;

}}



th {{

background:#0b3d91;

color:white;

padding:10px;

text-align:left;

}}



td {{

padding:9px;

border-bottom:1px solid #ddd;

vertical-align:top;

}}



tr:nth-child(even) {{

background:#f7f9fc;

}}



.alta {{

color:red;

font-weight:bold;

}}



.media {{

color:#d97706;

font-weight:bold;

}}


.footer {{

margin-top:25px;

font-size:12px;

color:#777;

text-align:center;

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
Informe generado:
{fecha_reporte}
</p>


</div>




<div class="cards">


<div class="card">

<strong>
{len(contratos)}
</strong>

<br>

Contratos tecnológicos

</div>



<div class="card">

<strong>
{len(procesos)}
</strong>

<br>

Procesos abiertos

</div>



<div class="card">

<strong>
{dinero(total_contratos)}
</strong>

<br>

Valor contratado

</div>



<div class="card">

<strong>
{entidades}
</strong>

<br>

Entidades

</div>



</div>





<h2>
🔐 Contratos tecnológicos detectados
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
Objeto
</th>


<th>
Valor
</th>


<th>
Proveedor
</th>


<th>
Fecha
</th>

</tr>



{filas_contratos}



</table>





<h2>
🚀 Nuevos procesos / oportunidades
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
Publicación
</th>


</tr>




{filas_procesos}




</table>



<div class="footer">

Fuente:
SECOP II · datos.gov.co

<br>

Monitor automático de oportunidades tecnológicas

</div>



</div>


</body>


</html>


"""


    return html
    # ======================================================
# GUARDAR INFORME HTML
# ======================================================


def guardar_html(html):


    nombre = (

        "informe_secop_tecnologia_"

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

        f"Informe guardado: {nombre}"

    )


    return nombre





# ======================================================
# ENVÍO DE CORREO
# ======================================================


def enviar_correo(

        html,

        contratos,

        procesos

):



    remitente = os.environ.get(

        "GMAIL_REMITENTE",

        ""

    )


    password = os.environ.get(

        "GMAIL_PASSWORD",

        ""

    )


    destinos = os.environ.get(

        "DESTINATARIOS",

        ""

    )




    if not remitente or not password:


        log(

            "❌ Faltan credenciales Gmail"

        )


        return




    lista = [

        correo.strip()

        for correo in destinos.split(",")

        if correo.strip()

    ]



    if not lista:


        log(

            "❌ No existen destinatarios"

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

                f"✅ Correo enviado: {destino}"

            )




        servidor.quit()



    except smtplib.SMTPAuthenticationError:



        log(

            "❌ Error autenticando Gmail"

        )


        log(

            "Usa una contraseña de aplicación"

        )


        sys.exit(1)




    except Exception as error:



        log(

            f"❌ Error enviando correo: {error}"

        )





# ======================================================
# EJECUCIÓN PRINCIPAL
# ======================================================


def main():



    log(

        "=" * 60

    )


    log(

        "🛡️ SECOP II Monitor Tecnología iniciado"

    )


    log(

        f"Días contratos: {CONFIG['dias_contratos']}"

    )


    log(

        f"Días procesos: {CONFIG['dias_procesos']}"

    )


    log(

        f"Palabras clave activas: {len(CONFIG['palabras_clave'])}"

    )


    log(

        "=" * 60

    )




    # ----------------------------
    # CONTRATOS
    # ----------------------------



    log(

        "Buscando contratos tecnológicos..."

    )



    contratos = obtener_contratos()



    contratos = enriquecer_contratos(

        contratos

    )



    log(

        f"Contratos encontrados: {len(contratos)}"

    )




    # ----------------------------
    # PROCESOS
    # ----------------------------



    log(

        "Buscando oportunidades..."

    )



    procesos = obtener_procesos()



    procesos = enriquecer_procesos(

        procesos

    )



    log(

        f"Procesos encontrados: {len(procesos)}"

    )




    # ----------------------------
    # HTML
    # ----------------------------



    log(

        "Generando informe HTML..."

    )



    html = generar_html(

        contratos,

        procesos

    )



    guardar_html(

        html

    )




    # ----------------------------
    # EMAIL
    # ----------------------------



    log(

        "Enviando informe..."

    )



    enviar_correo(

        html,

        contratos,

        procesos

    )




    log(

        "✅ Proceso terminado correctamente"

    )



    log(

        "=" * 60

    )





if __name__ == "__main__":


    main()
