from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date, datetime, timezone, timedelta
from typing import List
from app.database import get_db
from app import models, schemas

router = APIRouter()

TZ_TASHKENT = timezone(timedelta(hours=5))

def get_day_range(den: date):
    """Возвращает начало и конец дня по Ташкенту в UTC"""
    start = datetime(den.year, den.month, den.day, 0, 0, 0, tzinfo=TZ_TASHKENT).astimezone(timezone.utc).replace(tzinfo=None)
    end   = datetime(den.year, den.month, den.day, 23, 59, 59, tzinfo=TZ_TASHKENT).astimezone(timezone.utc).replace(tzinfo=None)
    return start, end

@router.post("/", response_model=schemas.PrikhodOut, summary="Добавить приход сырья")
def create_prikhod(data: schemas.PrikhodCreate, db: Session = Depends(get_db)):
    netto = data.brutto_kg - data.tara_kg
    if netto <= 0:
        raise HTTPException(400, "Нетто не может быть отрицательным")
    prikhod = models.PrikhodSyrya(**data.model_dump(), netto_kg=netto)
    db.add(prikhod)
    ostatok = db.query(models.Ostatok).filter_by(vid_syrya_id=data.vid_syrya_id).first()
    if ostatok:
        ostatok.kolichestvo_kg += netto
    else:
        ostatok = models.Ostatok(vid_syrya_id=data.vid_syrya_id, kolichestvo_kg=netto)
        db.add(ostatok)
    db.commit()
    db.refresh(prikhod)
    return prikhod

@router.get("/", response_model=List[schemas.PrikhodOut], summary="Список приходов")
def get_prikhod(den: date = None, vid_syrya_id: int = None, db: Session = Depends(get_db)):
    q = db.query(models.PrikhodSyrya)
    if den:
        start, end = get_day_range(den)
        q = q.filter(models.PrikhodSyrya.data_vremya >= start, models.PrikhodSyrya.data_vremya <= end)
    if vid_syrya_id:
        q = q.filter_by(vid_syrya_id=vid_syrya_id)
    return q.order_by(models.PrikhodSyrya.data_vremya.desc()).all()

@router.get("/itog-za-den", summary="Итог прихода за день по видам сырья")
def itog_prikhod(den: date = None, db: Session = Depends(get_db)):
    if not den:
        den = datetime.now(TZ_TASHKENT).date()
    start, end = get_day_range(den)
    rows = (
        db.query(
            models.VidSyrya.name,
            func.sum(models.PrikhodSyrya.netto_kg).label("itogo_kg"),
            func.count(models.PrikhodSyrya.id).label("mashin")
        )
        .join(models.VidSyrya, models.PrikhodSyrya.vid_syrya_id == models.VidSyrya.id)
        .filter(models.PrikhodSyrya.data_vremya >= start, models.PrikhodSyrya.data_vremya <= end)
        .group_by(models.VidSyrya.name).all()
    )
    return [{"vid_syrya": r.name, "itogo_kg": r.itogo_kg, "mashin": r.mashin} for r in rows]

@router.get("/{prikhod_id}", response_model=schemas.PrikhodOut)
def get_prikhod_one(prikhod_id: int, db: Session = Depends(get_db)):
    p = db.query(models.PrikhodSyrya).get(prikhod_id)
    if not p:
        raise HTTPException(404, "Запись не найдена")
    return p
