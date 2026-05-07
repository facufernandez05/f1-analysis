from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import router as api_v1_router
from app.config import settings

app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG,
    # La documentación interactiva queda en http://localhost:8000/docs
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registra todas las rutas de /api/v1/...
app.include_router(api_v1_router)


@app.get("/health", tags=["health"])
async def health():
    return {"status": "ok", "app": settings.APP_NAME}
