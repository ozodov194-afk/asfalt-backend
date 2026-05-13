from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, cast, Date, text
from datetime import date
from typing import List
from app.database import get_db
from app import models, schemas

router = APIRouter()

def tz_date(col):
    return cast(col + text("interval '5 hours'"), Date)

@router.post("/", response_model=schemas.ProizvodstvoOut, summary="Добавить партию асфальта")
def create_proizvodstvo(data: schemas.ProizvodstvoCreate, db: Session = Depends(get_db)):
    partiya = models.Proizvodstvo(**data.model_dump())
    db.add(partiya)
    db.commit()
    db.refresh(partiya)
    return partiya

@router.get("/", response_model=List[schemas.ProizvodstvoOut], summary="Список партий")
def get_proizvodstvo(den: date = None, marka_id: int = None, db: Session = Depends(get_db)):
    q = db.query(models.Proizvodstvo)
    if den:
        q = q.filter(tz_date(models.Proizvodstvo.data_vremya) == den)
    if marka_id:
        q = q.filter_by(marka_id=marka_id)
    return q.order_by(models.Proizvodstvo.data_vremya.desc()).all()

@router.get("/itog-za-den", summary="Итог производства за день по маркам")
def itog_proizvodstvo(den: date = None, db: Session = Depends(get_db)):
    if not den:
        den = date.today()
    rows = (
        db.query(
            models.MarkaAsfalta.name,
            func.sum(models.Proizvodstvo.ves_kg).label("itogo_kg"),
            func.count(models.Proizvodstvo.id).label("partiy"),
            func.avg(models.Proizvodstvo.temperatura).label("avg_temp")
        )
        .join(models.MarkaAsfalta)
        .filter(tz_date(models.Proizvodstvo.data_vremya) == den)
        .group_by(models.MarkaAsfalta.name)
        .all()
    )
    return [{"marka": r.name, "itogo_kg": round(r.itogo_kg, 1), "partiy": r.partiy,
             "avg_temperatura": round(r.avg_temp, 1) if r.avg_temp else None} for r in rows]
