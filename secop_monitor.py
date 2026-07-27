"""
SECOP II Monitor Automático
===========================

Consulta información pública de SECOP II mediante datos.gov.co
Genera informe HTML y envía correo automático.

Compatible con GitHub Actions.

Variables requeridas:
GMAIL_REMITENTE
GMAIL_PASSWORD
DESTINATARIOS
"""

import os
import sys
import smtplib
import requests

from datetime import datetime, timedelta
from pathlib import Path

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


# =====================================================
# CONFIGURACIÓN
# =====================================================

CONFIG = {

    # Filtros generales
    "departamento": "",
    "palabra_clave": "",

    # Días de búsqueda
    "dias_contratos": 15,
    "dias_procesos": 30,

    # Cantidad máxima
    "limite": 50,
}


# Dataset SECOP II

API_CONTRATOS = (
    "https://www.datos.gov.co/resource/jbjy-vk9h.json"
)

API_PROCESOS = (
    "https://www.datos.gov.co/resource/p6dx-8zbt.json"
)


HEADERS = {
    "Accept": "application/json"
}


# =====================================================
# UTILIDADES
# =====================================================

def log(texto):
    hora = datetime.now().strftime("%H:%M:%S")
    print(f"[{hora}] {texto}", flush=True)



def dinero(valor):

    try:
        valor = float(valor)

        if valor >= 1000000000:
            return f"${valor/1000000000:.1f} B"

        if valor >= 1000000:
            return f"${valor/1000000:.0f} M"

        return f"${valor:,.0f}"

    except:

        return "N/D"



def fecha(valor):

    if not valor:
        return "-"

    try:
        return valor[:10]

    except:

        return "-"



# =====================================================
# CONSULTA API
# =====================================================


def consultar(url, where="", order="", limite=50):

    parametros = {

        "$limit": limite

    }


    if where:
        parametros["$where"] = where


    if order:
        parametros["$order"] = order


    try:

        respuesta = requests.get(
            url,
            params=parametros,
            headers=HEADERS,
            timeout=40
        )


        log(f"Consulta: {respuesta.url}")


        respuesta.raise_for_status()


        datos = respuesta.json()


        log(
            f"Registros recibidos: {len(datos)}"
        )


        return datos


    except Exception as error:

        log(
            f"Error consultando API: {error}"
        )

        return []



# =====================================================
# CONTRATOS
# =====================================================


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


    if CONFIG["departamento"]:

        condiciones.append(
            "upper(departamento) like "
            f"upper('%{CONFIG['departamento']}%')"
        )


    if CONFIG["palabra_clave"]:

        condiciones.append(
            "upper(objeto_del_contrato) like "
            f"upper('%{CONFIG['palabra_clave']}%')"
        )


    where = " AND ".join(condiciones)


    return consultar(

        API_CONTRATOS,

        where,

        "valor_del_contrato DESC",

        CONFIG["limite"]

    )
  # =====================================================
# PROCESOS / LICITACIONES
# =====================================================


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


    if CONFIG["departamento"]:

        condiciones.append(
            "upper(departamento_entidad) like "
            f"upper('%{CONFIG['departamento']}%')"
        )


    if CONFIG["palabra_clave"]:

        condiciones.append(
            "upper(descripci_n_del_procedimiento) like "
            f"upper('%{CONFIG['palabra_clave']}%')"
        )


    where = " AND ".join(condiciones)


    return consultar(

        API_PROCESOS,

        where,

        "precio_base DESC",

        CONFIG["limite"]

    )



# =====================================================
# GENERADOR HTML
# =====================================================


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



    filas_contratos = ""


    for c in contratos:


        filas_contratos += f"""

        <tr>

        <td>
        {c.get('nombre_entidad','-')}
        </td>

        <td>
        {c.get('objeto_del_contrato','-')[:120]}
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
        <td colspan="5">
        No hay contratos encontrados
        </td>
        </tr>

        """



    filas_procesos = ""


    for p in procesos:


        filas_procesos += f"""


        <tr>

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
        )[:120]}
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
        <td colspan="4">
        No hay procesos encontrados
        </td>
        </tr>

        """



    html = f"""

<!DOCTYPE html>

<html>

<head>

<meta charset="utf-8">


<style>


body {{

font-family: Arial;

background:#f2f4f8;

padding:20px;

}}


.container {{

background:white;

max-width:1000px;

margin:auto;

padding:30px;

border-radius:10px;

}}


h1 {{

color:#123b70;

}}


.card {{

display:inline-block;

background:#eef4ff;

padding:15px;

margin:5px;

border-radius:8px;

text-align:center;

}}


table {{

width:100%;

border-collapse:collapse;

margin-top:20px;

}}


th {{

background:#123b70;

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


<div class="container">


<h1>
📋 Informe SECOP II
</h1>


<p>
Generado:
<b>{fecha_reporte}</b>
</p>


<div class="card">

<b>{len(contratos)}</b>
<br>
Contratos

</div>



<div class="card">

<b>{len(procesos)}</b>
<br>
Procesos

</div>



<div class="card">

<b>{dinero(total_contratos)}</b>
<br>
Valor contratos

</div>



<div class="card">

<b>{entidades}</b>
<br>
Entidades

</div>



<h2>
📝 Contratos recientes
</h2>


<table>


<tr>

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
Contratista
</th>

<th>
Fecha
</th>

</tr>


{filas_contratos}


</table>




<h2>
📢 Procesos de contratación
</h2>


<table>


<tr>

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



</div>


</body>

</html>


"""


    return html
# =====================================================
# GUARDAR INFORME HTML
# =====================================================


def guardar_html(html):

    nombre = (
        "informe_secop_"
        +
        datetime.now().strftime("%Y-%m-%d")
        +
        ".html"
    )


    Path(nombre).write_text(
        html,
        encoding="utf-8"
    )


    log(
        f"Archivo generado: {nombre}"
    )


    return nombre



# =====================================================
# ENVÍO DE CORREO
# =====================================================


def enviar_correo(html, contratos, procesos):


    remitente = os.environ.get(
        "GMAIL_REMITENTE",
        ""
    )


    password = os.environ.get(
        "GMAIL_PASSWORD",
        ""
    )


    lista_destinos = os.environ.get(
        "DESTINATARIOS",
        ""
    )



    if not remitente or not password:

        log(
            "Faltan credenciales Gmail"
        )

        return



    destinatarios = [

        x.strip()

        for x in lista_destinos.split(",")

        if x.strip()

    ]



    if not destinatarios:

        log(
            "No hay destinatarios configurados"
        )

        return



    asunto = (

        "📋 Informe SECOP II - "

        +

        datetime.now().strftime(
            "%d/%m/%Y"
        )

        +

        f" | {len(contratos)} contratos "
        +
        f"| {len(procesos)} procesos"

    )



    try:


        with smtplib.SMTP_SSL(
            "smtp.gmail.com",
            465
        ) as servidor:


            servidor.login(
                remitente,
                password
            )



            for correo in destinatarios:


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

                mensaje["To"] = correo



                mensaje.attach(

                    MIMEText(
                        html,
                        "html",
                        "utf-8"
                    )

                )



                servidor.sendmail(

                    remitente,

                    correo,

                    mensaje.as_string()

                )


                log(
                    f"Correo enviado a {correo}"
                )



    except smtplib.SMTPAuthenticationError:


        log(
            "Error Gmail: revisa la contraseña de aplicación"
        )


        sys.exit(1)



    except Exception as error:


        log(
            f"Error enviando correo: {error}"
        )



# =====================================================
# EJECUCIÓN PRINCIPAL
# =====================================================


def main():

    log(
        "=" * 50
    )

    log(
        "SECOP II Monitor iniciado"
    )


    log(
        f"Departamento: "
        f"{CONFIG['departamento'] or 'Todos'}"
    )


    log(
        f"Palabra clave: "
        f"{CONFIG['palabra_clave'] or 'Todas'}"
    )


    log(
        "=" * 50
    )



    log(
        "Consultando contratos..."
    )


    contratos = obtener_contratos()



    log(
        f"Contratos encontrados: {len(contratos)}"
    )



    log(
        "Consultando procesos..."
    )


    procesos = obtener_procesos()



    log(
        f"Procesos encontrados: {len(procesos)}"
    )



    log(
        "Generando informe..."
    )


    html = generar_html(
        contratos,
        procesos
    )



    guardar_html(html)



    log(
        "Enviando correo..."
    )


    enviar_correo(
        html,
        contratos,
        procesos
    )



    log(
        "Proceso terminado correctamente"
    )



if __name__ == "__main__":

    main()
# =====================================================
# GUARDAR INFORME HTML
# =====================================================


def guardar_html(html):

    nombre = (
        "informe_secop_"
        +
        datetime.now().strftime("%Y-%m-%d")
        +
        ".html"
    )


    Path(nombre).write_text(
        html,
        encoding="utf-8"
    )


    log(
        f"Archivo generado: {nombre}"
    )


    return nombre



# =====================================================
# ENVÍO DE CORREO
# =====================================================


def enviar_correo(html, contratos, procesos):


    remitente = os.environ.get(
        "GMAIL_REMITENTE",
        ""
    )


    password = os.environ.get(
        "GMAIL_PASSWORD",
        ""
    )


    lista_destinos = os.environ.get(
        "DESTINATARIOS",
        ""
    )



    if not remitente or not password:

        log(
            "Faltan credenciales Gmail"
        )

        return



    destinatarios = [

        x.strip()

        for x in lista_destinos.split(",")

        if x.strip()

    ]



    if not destinatarios:

        log(
            "No hay destinatarios configurados"
        )

        return



    asunto = (

        "📋 Informe SECOP II - "

        +

        datetime.now().strftime(
            "%d/%m/%Y"
        )

        +

        f" | {len(contratos)} contratos "
        +
        f"| {len(procesos)} procesos"

    )



    try:


        with smtplib.SMTP_SSL(
            "smtp.gmail.com",
            465
        ) as servidor:


            servidor.login(
                remitente,
                password
            )



            for correo in destinatarios:


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

                mensaje["To"] = correo



                mensaje.attach(

                    MIMEText(
                        html,
                        "html",
                        "utf-8"
                    )

                )



                servidor.sendmail(

                    remitente,

                    correo,

                    mensaje.as_string()

                )


                log(
                    f"Correo enviado a {correo}"
                )



    except smtplib.SMTPAuthenticationError:


        log(
            "Error Gmail: revisa la contraseña de aplicación"
        )


        sys.exit(1)



    except Exception as error:


        log(
            f"Error enviando correo: {error}"
        )



# =====================================================
# EJECUCIÓN PRINCIPAL
# =====================================================


def main():

    log(
        "=" * 50
    )

    log(
        "SECOP II Monitor iniciado"
    )


    log(
        f"Departamento: "
        f"{CONFIG['departamento'] or 'Todos'}"
    )


    log(
        f"Palabra clave: "
        f"{CONFIG['palabra_clave'] or 'Todas'}"
    )


    log(
        "=" * 50
    )



    log(
        "Consultando contratos..."
    )


    contratos = obtener_contratos()



    log(
        f"Contratos encontrados: {len(contratos)}"
    )



    log(
        "Consultando procesos..."
    )


    procesos = obtener_procesos()



    log(
        f"Procesos encontrados: {len(procesos)}"
    )



    log(
        "Generando informe..."
    )


    html = generar_html(
        contratos,
        procesos
    )



    guardar_html(html)



    log(
        "Enviando correo..."
    )


    enviar_correo(
        html,
        contratos,
        procesos
    )



    log(
        "Proceso terminado correctamente"
    )



if __name__ == "__main__":

    main()

