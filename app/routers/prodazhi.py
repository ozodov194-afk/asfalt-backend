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

@router.post("/", response_model=schemas.ProdazhaOut, summary="Добавить отгрузку")
def create_prodazha(data: schemas.ProdazhaCreate, db: Session = Depends(get_db)):
    netto = data.brutto_kg - data.tara_kg
    if netto <= 0:
        raise HTTPException(400, "Нетто не может быть отрицательным")
    summa = None
    if data.tsena_za_tonnu:
        summa = round((netto / 1000) * data.tsena_za_tonnu, 0)
    nakladnaya = data.nakladnaya_no
    if not nakladnaya:
        count = db.query(func.count(models.Prodazha.id)).scalar()
        nakladnaya = f"НК-{str(count + 1).zfill(5)}"
    prodazha = models.Prodazha(
        **{k: v for k, v in data.model_dump().items() if k != 'nakladnaya_no'},
        netto_kg=netto, summa=summa, nakladnaya_no=nakladnaya
    )
    db.add(prodazha)
    db.commit()
    db.refresh(prodazha)
    return prodazha

@router.get("/", response_model=List[schemas.ProdazhaOut], summary="Список продаж")
def get_prodazhi(den: date = None, pokupatel_id: int = None, db: Session = Depends(get_db)):
    q = db.query(models.Prodazha)
    if den:
        start, end = get_day_range(den)
        q = q.filter(models.Prodazha.data_vremya >= start, models.Prodazha.data_vremya <= end)
    if pokupatel_id:
        q = q.filter_by(pokupatel_id=pokupatel_id)
    return q.order_by(models.Prodazha.data_vremya.desc()).all()

@router.get("/itog-za-den", summary="Итог продаж за день")
def itog_prodazhi(den: date = None, db: Session = Depends(get_db)):
    if not den:
        den = datetime.now(TZ_TASHKENT).date()
    start, end = get_day_range(den)
    rows = (
        db.query(models.Pokupatel.name, func.sum(models.Prodazha.netto_kg).label("netto_kg"),
                 func.sum(models.Prodazha.summa).label("summa"), func.count(models.Prodazha.id).label("mashin"))
        .join(models.Pokupatel)
        .filter(models.Prodazha.data_vremya >= start, models.Prodazha.data_vremya <= end)
        .group_by(models.Pokupatel.name).all()
    )
    return [{"pokupatel": r.name, "netto_kg": round(r.netto_kg, 1), "summa": r.summa, "mashin": r.mashin} for r in rows]

@router.get("/po-pokupatelam", summary="Отчёт по покупателям за период")
def po_pokupatelam(date_from: date = None, date_to: date = None, db: Session = Depends(get_db)):
    q = (
        db.query(models.Pokupatel.name, func.sum(models.Prodazha.netto_kg).label("netto_kg"),
                 func.sum(models.Prodazha.summa).label("summa"), func.count(models.Prodazha.id).label("reysy"))
        .join(models.Pokupatel)
    )
    if date_from:
        start, _ = get_day_range(date_from)
        q = q.filter(models.Prodazha.data_vremya >= start)
    if date_to:
        _, end = get_day_range(date_to)
        q = q.filter(models.Prodazha.data_vremya <= end)
    rows = q.group_by(models.Pokupatel.name).order_by(func.sum(models.Prodazha.netto_kg).desc()).all()
    return [{"pokupatel": r.name, "netto_t": round(r.netto_kg/1000, 2), "summa": r.summa, "reysy": r.reysy} for r in rows]

@router.get("/avto/{gos_nomer}", summary="Найти покупателя по гос. номеру авто")
def avto_by_nomer(gos_nomer: str, db: Session = Depends(get_db)):
    avto = db.query(models.Avto).filter(models.Avto.gos_nomer == gos_nomer.upper().replace(" ", "")).first()
    if not avto:
        raise HTTPException(404, "Авто не найдено в базе")
    return {"avto_id": avto.id, "gos_nomer": avto.gos_nomer, "marka": avto.marka,
            "pokupatel_id": avto.pokupatel_id, "pokupatel": avto.pokupatel.name if avto.pokupatel else None}

@router.delete("/{prodazha_id}", summary="Удалить продажу")
def delete_prodazha(prodazha_id: int, db: Session = Depends(get_db)):
    p = db.query(models.Prodazha).get(prodazha_id)
    if not p:
        raise HTTPException(404, "Запись не найдена")
    db.delete(p)
    db.commit()
    return {"ok": True}
