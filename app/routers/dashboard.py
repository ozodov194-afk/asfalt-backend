from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date, datetime, timezone, timedelta
from app.database import get_db
from app import models

router = APIRouter()

TZ_TASHKENT = timezone(timedelta(hours=5))

def get_day_range(den: date):
    start = datetime(den.year, den.month, den.day, 0, 0, 0, tzinfo=TZ_TASHKENT).astimezone(timezone.utc).replace(tzinfo=None)
    end   = datetime(den.year, den.month, den.day, 23, 59, 59, tzinfo=TZ_TASHKENT).astimezone(timezone.utc).replace(tzinfo=None)
    return start, end

@router.get("/segodnya", summary="Все данные дашборда за сегодня")
def dashboard_segodnya(den: date = None, db: Session = Depends(get_db)):
    if not den:
        den = datetime.now(TZ_TASHKENT).date()

    start, end = get_day_range(den)

    prikhod = db.query(
        func.coalesce(func.sum(models.PrikhodSyrya.netto_kg), 0),
        func.count(models.PrikhodSyrya.id)
    ).filter(models.PrikhodSyrya.data_vremya >= start, models.PrikhodSyrya.data_vremya <= end).first()

    raskhod_rows = (
        db.query(models.VidSyrya.name, func.sum(models.RaskhodSyrya.fakt_kg).label("kg"))
        .join(models.VidSyrya)
        .filter(models.RaskhodSyrya.data_vremya >= start, models.RaskhodSyrya.data_vremya <= end)
        .group_by(models.VidSyrya.name).all()
    )

    proizvod = db.query(
        func.coalesce(func.sum(models.Proizvodstvo.ves_kg), 0),
        func.count(models.Proizvodstvo.id)
    ).filter(models.Proizvodstvo.data_vremya >= start, models.Proizvodstvo.data_vremya <= end).first()

    prod_marki = (
        db.query(models.MarkaAsfalta.name, func.sum(models.Proizvodstvo.ves_kg).label("kg"))
        .join(models.MarkaAsfalta)
        .filter(models.Proizvodstvo.data_vremya >= start, models.Proizvodstvo.data_vremya <= end)
        .group_by(models.MarkaAsfalta.name).all()
    )

    prodazhi = db.query(
        func.coalesce(func.sum(models.Prodazha.netto_kg), 0),
        func.coalesce(func.sum(models.Prodazha.summa), 0),
        func.count(func.distinct(models.Prodazha.pokupatel_id))
    ).filter(models.Prodazha.data_vremya >= start, models.Prodazha.data_vremya <= end).first()

    prikhod_vidy = (
        db.query(models.VidSyrya.name, func.sum(models.PrikhodSyrya.netto_kg).label("kg"),
                 func.count(models.PrikhodSyrya.id).label("mashin"))
        .join(models.VidSyrya)
        .filter(models.PrikhodSyrya.data_vremya >= start, models.PrikhodSyrya.data_vremya <= end)
        .group_by(models.VidSyrya.name).all()
    )

    ostatki = db.query(models.Ostatok, models.VidSyrya).join(models.VidSyrya).all()
    ostatki_data = []
    preduprejdeniya = []
    for ost, vid in ostatki:
        warn = vid.min_ostatok and ost.kolichestvo_kg < vid.min_ostatok
        ostatki_data.append({"name": vid.name, "kolichestvo_kg": round(ost.kolichestvo_kg, 1), "preduprejdenie": warn})
        if warn:
            preduprejdeniya.append(f"{vid.name}: осталось {round(ost.kolichestvo_kg,1)} кг (мин: {vid.min_ostatok})")

    poslednie = []
    for p in db.query(models.PrikhodSyrya).order_by(models.PrikhodSyrya.data_vremya.desc()).limit(3):
        poslednie.append({"tip": "prikhod", "vremya": str(p.data_vremya), "netto_kg": p.netto_kg})
    for p in db.query(models.Prodazha).order_by(models.Prodazha.data_vremya.desc()).limit(3):
        poslednie.append({"tip": "prodazha", "vremya": str(p.data_vremya), "netto_kg": p.netto_kg, "summa": p.summa})

    return {
        "den": str(den),
        "prikhod": {"itogo_kg": round(prikhod[0], 1), "mashin": prikhod[1],
                    "po_vidam": [{"vid": r.name, "kg": round(r.kg, 1), "mashin": r.mashin} for r in prikhod_vidy]},
        "raskhod": {"po_vidam": [{"vid": r.name, "kg": round(r.kg, 1)} for r in raskhod_rows]},
        "proizvodstvo": {"itogo_kg": round(proizvod[0], 1), "partiy": proizvod[1],
                         "po_markam": [{"marka": r.name, "kg": round(r.kg, 1)} for r in prod_marki]},
        "prodazhi": {"itogo_kg": round(prodazhi[0], 1), "vyruchka": round(prodazhi[1], 0), "pokupatelei": prodazhi[2]},
        "ostatki": ostatki_data,
        "preduprejdeniya": preduprejdeniya,
        "poslednie_operatsii": sorted(poslednie, key=lambda x: x["vremya"], reverse=True)[:5]
    }
