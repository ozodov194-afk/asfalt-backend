from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base
from app.routers import prikhod, raskhod, proizvodstvo, prodazhi, sklad, dashboard

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="АсфальтУчёт API",
    description="Система учёта асфальтового завода",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(prikhod.router,       prefix="/api/prikhod",      tags=["Приход сырья"])
app.include_router(raskhod.router,       prefix="/api/raskhod",      tags=["Расход сырья"])
app.include_router(proizvodstvo.router,  prefix="/api/proizvodstvo",  tags=["Производство"])
app.include_router(prodazhi.router,      prefix="/api/prodazhi",      tags=["Продажи"])
app.include_router(sklad.router,         prefix="/api/sklad",         tags=["Склад"])
app.include_router(dashboard.router,     prefix="/api/dashboard",     tags=["Дашборд"])

@app.get("/")
def root():
    return {"status": "ok", "app": "АсфальтУчёт v1.0"}
