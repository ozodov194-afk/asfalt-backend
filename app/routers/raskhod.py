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
    start = datetime(den.year, den.month, den.day, 0, 0, 0, tzinfo=TZ_TASHKENT).astimezone(timezone.utc).replace(tzinfo=None)
    end   = datetime(den.year, den.month, den.day, 23, 59, 59, tzinfo=TZ_TASHKENT).astimezone(timezone.utc).replace(tzinfo=None)
    return start, end

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
    db.commit()
    db.refresh(raskhod)
    return schemas.RaskhodOut.model_validate(raskhod)

@router.get("/", response_model=List[schemas.RaskhodOut], summary="Список расходов")
def get_raskhod(den: date = None, vid_syrya_id: int = None, db: Session = Depends(get_db)):
    q = db.query(models.RaskhodSyrya)
    if den:
        start, end = get_day_range(den)
        q = q.filter(models.RaskhodSyrya.data_vremya >= start, models.RaskhodSyrya.data_vremya <= end)
    if vid_syrya_id:
        q = q.filter_by(vid_syrya_id=vid_syrya_id)
    return q.order_by(models.RaskhodSyrya.data_vremya.desc()).all()

@router.get("/itog-za-den", summary="Итог расхода за день по видам сырья")
def itog_raskhod(den: date = None, db: Session = Depends(get_db)):
    if not den:
        den = datetime.now(TZ_TASHKENT).date()
    start, end = get_day_range(den)
    rows = (
        db.query(models.VidSyrya.name, func.sum(models.RaskhodSyrya.fakt_kg).label("itogo_kg"))
        .join(models.VidSyrya)
        .filter(models.RaskhodSyrya.data_vremya >= start, models.RaskhodSyrya.data_vremya <= end)
        .group_by(models.VidSyrya.name).all()
    )
    return [{"vid_syrya": r.name, "itogo_kg": r.itogo_kg} for r in rows]

@router.delete("/{raskhod_id}", summary="Удалить расход")
def delete_raskhod(raskhod_id: int, db: Session = Depends(get_db)):
    r = db.query(models.RaskhodSyrya).get(raskhod_id)
    if not r:
        raise HTTPException(404, "Запись не найдена")
    # Вернуть на склад
    ostatok = db.query(models.Ostatok).filter_by(vid_syrya_id=r.vid_syrya_id).first()
    if ostatok:
        ostatok.kolichestvo_kg += r.fakt_kg
    db.delete(r)
    db.commit()
    return {"ok": True}
