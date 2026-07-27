"""
SECOP II Monitor Inteligente Tecnología
=======================================

Busca oportunidades de contratación relacionadas con:

- Ciberseguridad
- SOC
- Centros de control
- Monitoreo
- CCTV
- Data Center
- Cloud
- Biometría
- ABIS
- Reconocimiento facial
- IA
- Analítica
- Infraestructura TI

Arquitectura:
SECOP API -> Python -> Filtros inteligentes -> HTML -> Gmail
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
# CONFIGURACIÓN
# ======================================================


CONFIG = {


    # Colombia completa
    "departamento": "",


    # Días hacia atrás

    "dias_contratos": 90,

    "dias_procesos": 90,


    # Cantidad descargada desde SECOP

    "limite_api": 500,


    # Cantidad mostrada en informe

    "limite_informe": 50,


}



# ======================================================
# PALABRAS CLAVE TECNOLOGÍA
# ======================================================


PALABRAS_ALTA = [

    "ciberseguridad",

    "seguridad informatica",

    "seguridad informática",

    "soc",

    "centro de operaciones de seguridad",

    "siem",

    "biometria",

    "biometría",

    "abis",

    "mega matcher",

    "verilook",

    "neurotechnology",

    "reconocimiento facial",

    "identificacion biometrica",

    "identificación biométrica",

    "control de acceso",

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

    "virtualizacion",

    "virtualización",

    "redes",

    "telecomunicaciones",

    "infraestructura ti",

    "infraestructura tecnológica",

]



PALABRAS_GENERAL = [

    "software",

    "hardware",

    "tecnologia",

    "tecnología",

    "sistema de información",

    "aplicativo",

    "plataforma",

    "digital",

    "automatización",

    "automatizacion",

    "inteligencia artificial",

    "ia",

    "analitica",

    "analítica",

    "big data",

    "monitoreo",

    "centro de control",

    "videovigilancia",

    "cctv",

]



# ======================================================
# APIS SECOP
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


def log(texto):

    hora = datetime.now().strftime("%H:%M:%S")

    print(
        f"[{hora}] {texto}",
        flush=True
    )




def dinero(valor):

    try:

        numero = float(valor)


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




def limpiar_texto(texto):

    if not texto:

        return ""


    return str(texto).lower()




def fecha(valor):

    if not valor:

        return "-"


    return str(valor)[:10]
# ======================================================
# CONSULTA SECOP SIN FILTROS SQL COMPLEJOS
# ======================================================


def consultar_secop(url, limite):


    try:


        respuesta = requests.get(

            url,

            params={

                "$limit": limite

            },

            headers=HEADERS,

            timeout=60

        )


        respuesta.raise_for_status()


        datos = respuesta.json()



        log(

            f"Registros descargados: {len(datos)}"

        )


        return datos



    except Exception as error:


        log(

            f"Error consultando SECOP: {error}"

        )


        return []





# ======================================================
# BUSCADOR INTELIGENTE DE CAMPOS
# ======================================================


def texto_registro(registro):


    campos = [

        "nombre_entidad",

        "entidad",

        "objeto_del_contrato",

        "descripcion_del_proceso",

        "descripci_n_del_procedimiento",

        "detalle_del_proceso",

        "objeto",

        "modalidad_de_contratacion",

        "proveedor_adjudicado",

        "razon_social"

    ]



    texto = []



    for campo in campos:


        valor = registro.get(campo)


        if valor:


            texto.append(

                str(valor)

            )



    return limpiar_texto(

        " ".join(texto)

    )





# ======================================================
# CLASIFICACIÓN DE OPORTUNIDAD
# ======================================================


def analizar_oportunidad(registro):


    texto = texto_registro(

        registro

    )



    resultado = {


        "nivel": "🟢 Normal",

        "coincidencias": []

    }



    for palabra in PALABRAS_ALTA:


        if palabra in texto:


            resultado["nivel"] = "🔴 Alta"


            resultado["coincidencias"].append(

                palabra

            )




    if resultado["nivel"] != "🔴 Alta":


        for palabra in PALABRAS_MEDIA:


            if palabra in texto:


                resultado["nivel"] = "🟠 Media"


                resultado["coincidencias"].append(

                    palabra

                )




    for palabra in PALABRAS_GENERAL:


        if palabra in texto:


            resultado["coincidencias"].append(

                palabra

            )



    return resultado





# ======================================================
# FILTRAR OPORTUNIDADES
# ======================================================


def filtrar_oportunidades(registros):


    encontrados = []



    for registro in registros:



        analisis = analizar_oportunidad(

            registro

        )



        # Solo guardar si encontró tecnología


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

        "Descargando contratos SECOP..."

    )



    registros = consultar_secop(

        API_CONTRATOS,

        CONFIG["limite_api"]

    )



    resultados = filtrar_oportunidades(

        registros

    )



    log(

        f"Contratos tecnológicos encontrados: {len(resultados)}"

    )



    return resultados





# ======================================================
# OBTENER PROCESOS ABIERTOS
# ======================================================


def obtener_procesos():



    log(

        "Descargando procesos SECOP..."

    )



    registros = consultar_secop(

        API_PROCESOS,

        CONFIG["limite_api"]

    )



    resultados = filtrar_oportunidades(

        registros

    )



    log(

        f"Oportunidades encontradas: {len(resultados)}"

    )



    return resultados
    # ======================================================
# GENERADOR HTML
# ======================================================


def generar_html(contratos, procesos):


    fecha_reporte = datetime.now().strftime(
        "%d/%m/%Y %H:%M"
    )



    total = 0



    for c in contratos:


        try:

            total += float(

                c.get(
                    "valor_del_contrato",
                    0
                )

                or 0

            )


        except:

            pass




    def fila(registro):


        nombre = (

            registro.get(
                "nombre_entidad"
            )

            or

            registro.get(
                "entidad"
            )

            or "-"

        )



        descripcion = (

            registro.get(
                "objeto_del_contrato"
            )

            or

            registro.get(
                "descripci_n_del_procedimiento"
            )

            or

            registro.get(
                "descripcion_del_proceso"
            )

            or "-"

        )



        valor = (

            registro.get(
                "valor_del_contrato"
            )

            or

            registro.get(
                "precio_base"
            )

            or 0

        )



        return f"""

        <tr>

        <td>
        {registro.get('prioridad','')}
        </td>


        <td>
        {nombre}
        </td>


        <td>
        {descripcion[:150]}
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


        </tr>

        """




    filas_contratos = "".join(

        fila(c)

        for c in contratos[:CONFIG["limite_informe"]]

    )



    filas_procesos = "".join(

        fila(p)

        for p in procesos[:CONFIG["limite_informe"]]

    )





    if not filas_contratos:


        filas_contratos = """

        <tr>

        <td colspan="5">

        No se encontraron contratos tecnológicos

        </td>

        </tr>

        """



    if not filas_procesos:


        filas_procesos = """

        <tr>

        <td colspan="5">

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

font-family:
Arial, sans-serif;

background:#f1f5f9;

padding:20px;

}}



.contenedor {{

max-width:1200px;

margin:auto;

background:white;

padding:30px;

border-radius:15px;

box-shadow:
0 5px 20px rgba(0,0,0,.15);

}}



.cabecera {{

background:
linear-gradient(
135deg,
#003566,
#0077b6
);

color:white;

padding:25px;

border-radius:12px;

}}



.tarjetas {{

display:flex;

gap:15px;

margin:20px 0;

flex-wrap:wrap;

}}



.tarjeta {{

background:#eaf4ff;

padding:20px;

border-radius:10px;

min-width:180px;

text-align:center;

}}



.tarjeta b {{

font-size:26px;

color:#003566;

}}



table {{

width:100%;

border-collapse:collapse;

font-size:13px;

}}



th {{

background:#003566;

color:white;

padding:10px;

text-align:left;

}}



td {{

padding:10px;

border-bottom:
1px solid #ddd;

vertical-align:top;

}}



tr:nth-child(even) {{

background:#f8fafc;

}}



.footer {{

margin-top:30px;

text-align:center;

font-size:12px;

color:#777;

}}


</style>


</head>



<body>


<div class="contenedor">



<div class="cabecera">


<h1>
🛡️ Monitor SECOP II Tecnología
</h1>


<p>
Generado:
{fecha_reporte}
</p>


</div>




<div class="tarjetas">


<div class="tarjeta">

<b>
{len(contratos)}
</b>

<br>

Contratos detectados

</div>



<div class="tarjeta">

<b>
{len(procesos)}
</b>

<br>

Procesos encontrados

</div>



<div class="tarjeta">

<b>
{dinero(total)}
</b>

<br>

Valor contratado

</div>



</div>





<h2>
📌 Contratos tecnológicos
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
Detectado por
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
Detectado por
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

        f"Archivo generado: {nombre}"

    )


    return nombre





# ======================================================
# ENVÍO DE CORREO GMAIL
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

            "❌ Faltan credenciales Gmail"

        )


        return




    lista = [

        x.strip()

        for x in destinatarios.split(",")

        if x.strip()

    ]



    if not lista:


        log(

            "❌ No hay destinatarios configurados"

        )


        return




    asunto = (

        "🛡️ SECOP Tecnología "

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




        for correo in lista:


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

                f"✅ Enviado a {correo}"

            )




        servidor.quit()



    except smtplib.SMTPAuthenticationError:


        log(

            "❌ Gmail rechazó autenticación"

        )


        log(

            "Usa una contraseña de aplicación Gmail"

        )



    except Exception as error:


        log(

            f"❌ Error enviando correo: {error}"

        )





# ======================================================
# PROCESO PRINCIPAL
# ======================================================


def main():


    log(

        "=" * 60

    )


    log(

        "🛡️ SECOP Monitor Tecnología iniciado"

    )


    log(

        "=" * 60

    )




    # Descargar contratos


    contratos = obtener_contratos()




    # Descargar procesos


    procesos = obtener_procesos()




    log(

        "Generando informe..."

    )



    html = generar_html(

        contratos,

        procesos

    )



    guardar_html(

        html

    )




    log(

        "Enviando correo..."

    )



    enviar_correo(

        html,

        contratos,

        procesos

    )




    log(

        "✅ Finalizado correctamente"

    )


    log(

        "=" * 60

    )





if __name__ == "__main__":


    main()
