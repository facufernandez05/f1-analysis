# F1 Telemetry API

API de telemetría de Fórmula 1 construida con Python y FastAPI.  
Proyecto de portafolio para aprender análisis de datos, Docker y CI/CD.

---

## Estructura del proyecto

```
f1-analysis/
├── app/                    # Código fuente de la API
│   ├── __init__.py
│   ├── main.py             # Punto de entrada de FastAPI (rutas, middlewares)
│   └── config.py           # Variables de configuración (leídas desde .env)
├── tests/                  # Tests automáticos
│   └── test_health.py
├── scripts/                # Scripts auxiliares de análisis y exploración
│   └── telemetry_check.py
├── data/                   # Caché local de fastf1 (ignorado en git)
├── notebooks/              # Notebooks de exploración (próximamente)
├── .github/workflows/      # CI/CD con GitHub Actions
│   └── ci.yml
├── Dockerfile              # Imagen Docker de la API
├── docker-compose.dev.yml  # Stack completo para desarrollo (API + PostgreSQL)
├── requirements.txt        # Dependencias Python
├── pyproject.toml          # Configuración de herramientas (pytest, ruff, black)
└── .env.example            # Plantilla de variables de entorno (crear .env local)
```

---

## Conceptos clave que vas a aprender en este proyecto

### ¿Qué es FastAPI?
Framework web de Python. Permite crear APIs HTTP de forma rápida.  
Cuando hacés `curl http://localhost:8000/health`, estás llamando a un **endpoint** definido en `app/main.py`.

### ¿Qué es Docker?
Herramienta que empaqueta tu aplicación con todo lo que necesita para correr  
(Python, librerías, configuración) en un contenedor aislado del resto del sistema.  
Así cualquier persona puede correr el proyecto con un solo comando, sin importar su OS.

### ¿Qué es docker-compose?
Permite levantar **múltiples contenedores juntos**. En este proyecto:
- Un contenedor con la API (FastAPI)
- Un contenedor con la base de datos (PostgreSQL)
- Ambos se comunican entre sí por una red interna de Docker

### ¿Qué es CI/CD?
- **CI (Continuous Integration)**: cada vez que hacés un commit o PR, GitHub  
  corre automáticamente los tests y el linter. Si algo está roto, te avisa antes  
  de que llegue a producción.
- **CD (Continuous Deployment)**: cuando el CI pasa, el deploy al servidor  
  se hace automáticamente (lo configuramos en iteraciones siguientes).

---

## Cómo correr el proyecto

### Opción A: Con Docker (recomendada, replica producción)

Necesitás tener instalado: **Docker** y **docker-compose** (vienen juntos con Docker Desktop).

```bash
# 1. Cloná o posicionarte en la carpeta del proyecto
cd f1-analysis

# 2. Levantá el stack completo (API + base de datos)
docker compose -f docker-compose.dev.yml up --build

# La primera vez tarda más porque descarga las imágenes base.
# Vas a ver logs de PostgreSQL y de uvicorn (servidor de FastAPI).

# 3. Verificá que la API responde (en otra terminal)
curl http://localhost:8000/health
# Respuesta esperada: {"status":"ok","app":"F1 Telemetry API"}

# 4. Para detener todo
docker compose -f docker-compose.dev.yml down
```

### Opción B: Sin Docker (más rápida para desarrollo)

```bash
# 1. Creá un entorno virtual de Python (aísla las dependencias del proyecto)
python3 -m venv .venv

# 2. Activá el entorno virtual
source .venv/bin/activate       # Linux/Mac
# .venv\Scripts\activate        # Windows

# 3. Instalá las dependencias
pip install -r requirements.txt

# 4. Corré la API (sin base de datos por ahora)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# --reload hace que la API se reinicie automáticamente cuando modificás código

# 5. Verificá que responde
curl http://localhost:8000/health
```

---

## Cómo correr los tests

```bash
# Con el entorno virtual activado:
pytest tests/ -v

# -v = verbose, muestra cada test con su resultado
# El output debería mostrar: tests/test_health.py::test_health PASSED
```

Los tests verifican que la API se comporta como se espera **sin necesitar levantar**  
la base de datos ni el servidor real. Esto los hace rápidos y reproducibles.

---

## Cómo correr el linter

El linter detecta errores de estilo y bugs simples antes de que lleguen a producción.

```bash
# Con el entorno virtual activado:
ruff check .        # Detecta problemas
black --check .     # Verifica formato
```

El CI en GitHub Actions corre esto automáticamente en cada PR.

---

## Variables de entorno

Creá un archivo `.env` en la raíz (nunca se sube a git):

```
APP_NAME=F1 Telemetry API
DEBUG=true
DATABASE_URL=postgresql://f1user:f1pass@localhost:5432/f1telemetry
```

Cuando usás docker-compose, estas variables ya están configuradas en el archivo.

---

## Roadmap

| # | Iteración | Estado |
|---|-----------|--------|
| 1 | Skeleton + Docker + CI | Completada |
| 2 | Modelos de datos (SQLAlchemy + Alembic) + endpoints CRUD | Pendiente |
| 3 | Script de ingesta con fastf1 | Pendiente |
| 4 | Análisis: comparación de vueltas por sector | Pendiente |
| 5 | CI completo + Docker builds de producción | Pendiente |
| 6 | CD: despliegue automático a staging | Pendiente |
| 7 | Extras: análisis de degradación de neumáticos, etc. | Pendiente |

---

## Stack

| Herramienta | Para qué |
|-------------|----------|
| Python 3.11+ | Lenguaje base |
| FastAPI | Framework HTTP para la API |
| SQLAlchemy | ORM para interactuar con la base de datos |
| Alembic | Migraciones de esquema de base de datos |
| PostgreSQL | Base de datos relacional |
| fastf1 | Librería para descargar telemetría de F1 |
| pytest | Tests automáticos |
| ruff + black | Linter y formateador de código |
| Docker | Contenerización |
| GitHub Actions | CI/CD automatizado |