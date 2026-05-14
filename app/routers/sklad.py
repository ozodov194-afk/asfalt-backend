from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from app.database import get_db
from app import models

router = APIRouter()

# ─── СХЕМЫ ────────────────────────────────────────────────────

class VidSyryaCreate(BaseModel):
    name: str
    edinitsa: str = "кг"
    min_ostatok: float = 0

class PostavshikCreate(BaseModel):
    name: str
    telefon: Optional[str] = None
    inn: Optional[str] = None

class PokupatelCreate(BaseModel):
    name: str
    telefon: Optional[str] = None
    inn: Optional[str] = None
    adres: Optional[str] = None

class MarkaCreate(BaseModel):
    name: str
    kod: Optional[str] = None

class AvtoCreate(BaseModel):
    gos_nomer: str
    pokupatel_id: Optional[int] = None
    postavshik_id: Optional[int] = None
    marka: Optional[str] = None
    gruzopod_kg: Optional[float] = None

# ─── ВИДЫ СЫРЬЯ ───────────────────────────────────────────────

@router.get("/vidy-syrya", summary="Список видов сырья")
def get_vidy_syrya(db: Session = Depends(get_db)):
    return db.query(models.VidSyrya).all()

@router.post("/vidy-syrya", summary="Добавить вид сырья")
def create_vid_syrya(data: VidSyryaCreate, db: Session = Depends(get_db)):
    obj = models.VidSyrya(**data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

@router.delete("/vidy-syrya/{id}", summary="Удалить вид сырья")
def delete_vid_syrya(id: int, db: Session = Depends(get_db)):
    obj = db.query(models.VidSyrya).get(id)
    if not obj:
        raise HTTPException(404, "Не найдено")
    db.delete(obj)
    db.commit()
    return {"ok": True}

# ─── ПОСТАВЩИКИ ───────────────────────────────────────────────

@router.get("/postavshiki", summary="Список поставщиков")
def get_postavshiki(db: Session = Depends(get_db)):
    return db.query(models.Postavshik).all()

@router.post("/postavshiki", summary="Добавить поставщика")
def create_postavshik(data: PostavshikCreate, db: Session = Depends(get_db)):
    obj = models.Postavshik(**data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

@router.delete("/postavshiki/{id}", summary="Удалить поставщика")
def delete_postavshik(id: int, db: Session = Depends(get_db)):
    obj = db.query(models.Postavshik).get(id)
    if not obj:
        raise HTTPException(404, "Не найдено")
    db.delete(obj)
    db.commit()
    return {"ok": True}

# ─── ПОКУПАТЕЛИ ───────────────────────────────────────────────

@router.get("/pokupateli", summary="Список покупателей")
def get_pokupateli(db: Session = Depends(get_db)):
    return db.query(models.Pokupatel).all()

@router.post("/pokupateli", summary="Добавить покупателя")
def create_pokupatel(data: PokupatelCreate, db: Session = Depends(get_db)):
    obj = models.Pokupatel(**data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

@router.delete("/pokupateli/{id}", summary="Удалить покупателя")
def delete_pokupatel(id: int, db: Session = Depends(get_db)):
    obj = db.query(models.Pokupatel).get(id)
    if not obj:
        raise HTTPException(404, "Не найдено")
    db.delete(obj)
    db.commit()
    return {"ok": True}

# ─── МАРКИ АСФАЛЬТА ───────────────────────────────────────────

@router.get("/marki-asfalta", summary="Список марок асфальта")
def get_marki(db: Session = Depends(get_db)):
    return db.query(models.MarkaAsfalta).all()

@router.post("/marki-asfalta", summary="Добавить марку асфальта")
def create_marka(data: MarkaCreate, db: Session = Depends(get_db)):
    obj = models.MarkaAsfalta(**data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

@router.delete("/marki-asfalta/{id}", summary="Удалить марку")
def delete_marka(id: int, db: Session = Depends(get_db)):
    obj = db.query(models.MarkaAsfalta).get(id)
    if not obj:
        raise HTTPException(404, "Не найдено")
    db.delete(obj)
    db.commit()
    return {"ok": True}

# ─── АВТОМОБИЛИ ───────────────────────────────────────────────

@router.get("/avto", summary="Список автомобилей")
def get_avto(db: Session = Depends(get_db)):
    avto_list = db.query(models.Avto).all()
    return [
        {
            "id": a.id,
            "gos_nomer": a.gos_nomer,
            "marka": a.marka,
            "gruzopod_kg": a.gruzopod_kg,
            "pokupatel_id": a.pokupatel_id,
            "pokupatel": a.pokupatel.name if a.pokupatel else None,
            "postavshik_id": a.postavshik_id,
            "postavshik": a.postavshik.name if a.postavshik else None,
        }
        for a in avto_list
    ]

@router.post("/avto", summary="Добавить автомобиль")
def create_avto(data: AvtoCreate, db: Session = Depends(get_db)):
    gos = data.gos_nomer.upper().replace(" ", "")
    existing = db.query(models.Avto).filter_by(gos_nomer=gos).first()
    if existing:
        raise HTTPException(400, f"Авто {gos} уже существует в базе")
    obj = models.Avto(**{**data.model_dump(), "gos_nomer": gos})
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

@router.delete("/avto/{id}", summary="Удалить автомобиль")
def delete_avto(id: int, db: Session = Depends(get_db)):
    obj = db.query(models.Avto).get(id)
    if not obj:
        raise HTTPException(404, "Не найдено")
    db.delete(obj)
    db.commit()
    return {"ok": True}

# ─── ОСТАТКИ СКЛАДА ───────────────────────────────────────────

@router.get("/ostatki", summary="Остатки сырья на складе")
def get_ostatki(db: Session = Depends(get_db)):
    rows = (
        db.query(models.Ostatok, models.VidSyrya)
        .join(models.VidSyrya)
        .all()
    )
    result = []
    for ost, vid in rows:
        warn = ost.kolichestvo_kg < vid.min_ostatok if vid.min_ostatok else False
        result.append({
            "vid_syrya_id": vid.id,
            "name": vid.name,
            "kolichestvo_kg": round(ost.kolichestvo_kg, 1),
            "min_ostatok": vid.min_ostatok,
            "preduprejdenie": warn,
            "obnovleno": ost.obnovleno
        })
    return result
