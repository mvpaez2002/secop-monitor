# 📋 SECOP Monitor — GitHub Actions

Monitoreo automático de contratación pública colombiana (SECOP II).  
Corre en la nube gratis, de lunes a viernes a las **7:00 AM** hora Colombia.

---

## ¿Qué hace?

- Consulta la API de **datos.gov.co** (SECOP II)
- Obtiene contratos recientes y licitaciones abiertas
- Genera un **informe HTML** profesional
- Lo **envía por correo** a todos los destinatarios configurados
- Guarda el HTML como artefacto descargable en GitHub

---

## Configuración (5 minutos)

### 1. Crea el repositorio en GitHub

- Sube estos archivos a un repo nuevo (puede ser privado)

### 2. Configura los GitHub Secrets

Ve a tu repo → **Settings → Secrets and variables → Actions → New repository secret**

| Secret | Valor |
|--------|-------|
| `GMAIL_REMITENTE` | tu cuenta Gmail que envía (ej: `monitor@gmail.com`) |
| `GMAIL_PASSWORD` | [contraseña de aplicación Gmail](https://myaccount.google.com/apppasswords) — 16 caracteres, **no** tu contraseña normal |
| `DESTINATARIOS` | correos separados por coma: `a@empresa.com,b@otro.com,c@correo.com` |

> **Contraseña de aplicación Gmail:** ve a [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords), selecciona "Correo" y "Otro (nombre personalizado)", ponle "SECOP Monitor" y copia los 16 caracteres que genera.

### 3. Ajusta los filtros (opcional)

Edita `secop_monitor.py` y modifica el bloque `FILTROS`:

```python
FILTROS = {
    "departamento": "Cundinamarca",  # vacío = toda Colombia
    "sector":       "salud",         # vacío = todos los sectores
    "dias":         1,               # contratos de los últimos N días
    "dias_licit":   30,              # licitaciones de los últimos N días
    "limite":       50,              # máx. registros por consulta
}
```

### 4. Ejecuta manualmente para probar

Ve a **Actions → SECOP Monitor Diario → Run workflow** y verifica que llegan los correos.

---

## Horario

```
Lunes a viernes — 7:00 AM hora Colombia (12:00 UTC)
```

Para cambiar el horario, edita `.github/workflows/secop_diario.yml`:
```yaml
- cron: '0 12 * * 1-5'   # formato: minuto hora día mes día_semana
```

---

## Artefactos

Cada ejecución guarda el HTML en **Actions → tu ejecución → Artifacts** (se conservan 30 días).

---

## Fuente de datos

- **Contratos:** [jbjy-vk9h](https://www.datos.gov.co/resource/jbjy-vk9h.json) — SECOP II
- **Licitaciones:** [p6dx-8zbt](https://www.datos.gov.co/resource/p6dx-8zbt.json) — SECOP II
- API pública SODA — Colombia Compra Eficiente
