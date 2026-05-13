from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, cast, Date
from datetime import date
from typing import List
from app.database import get_db
from app import models, schemas

router = APIRouter()

TZ = 'Asia/Tashkent'

def tz_date(col):
    return func.date(func.timezone(TZ, col))

@router.post("/", response_model=schemas.RaskhodOut, summary="Добавить расход сырья")
def create_raskhod(data: schemas.RaskhodCreate, db: Session = Depends(get_db)):
    ostatok = db.query(models.Ostatok).filter_by(vid_syrya_id=data.vid_syrya_id).first()
    if not ostatok or ostatok.kolichestvo_kg < data.fakt_kg:
        raise HTTPException(400, "Недостаточно сырья на складе")
    otklonenie = None
    if data.norma_kg and data.norma_kg > 0:
        otklonenie = round((data.fakt_kg - data.norma_kg) / data.norma_kg * 100, 2)
    raskhod = models.RaskhodSyrya(**data.model_dump(), otklonenie_pct=otklonenie)
    db.add(raskhod)
    ostatok.kolichestvo_kg -= data.fakt_kg
    vid = db.query(models.VidSyrya).get(data.vid_syrya_id)
    if vid and ostatok.kolichestvo_kg < vid.min_ostatok:
        pass
    db.commit()
    db.refresh(raskhod)
    return schemas.RaskhodOut.model_validate(raskhod)

@router.get("/", response_model=List[schemas.RaskhodOut], summary="Список расходов")
def get_raskhod(den: date = None, vid_syrya_id: int = None, db: Session = Depends(get_db)):
    q = db.query(models.RaskhodSyrya)
    if den:
        q = q.filter(tz_date(models.RaskhodSyrya.data_vremya) == den)
    if vid_syrya_id:
        q = q.filter_by(vid_syrya_id=vid_syrya_id)
    return q.order_by(models.RaskhodSyrya.data_vremya.desc()).all()

@router.get("/itog-za-den", summary="Итог расхода за день по видам сырья")
def itog_raskhod(den: date = None, db: Session = Depends(get_db)):
    if not den:
        den = date.today()
    rows = (
        db.query(models.VidSyrya.name, func.sum(models.RaskhodSyrya.fakt_kg).label("itogo_kg"))
        .join(models.VidSyrya)
        .filter(tz_date(models.RaskhodSyrya.data_vremya) == den)
        .group_by(models.VidSyrya.name)
        .all()
    )
    return [{"vid_syrya": r.name, "itogo_kg": r.itogo_kg} for r in rows]
