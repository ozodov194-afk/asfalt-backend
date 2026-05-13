from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import enum

# ─── СПРАВОЧНИКИ ───────────────────────────────────────────────

class Postavshik(Base):
    """Поставщики сырья"""
    __tablename__ = "postavshiki"
    id        = Column(Integer, primary_key=True)
    name      = Column(String(200), nullable=False)
    telefon   = Column(String(20))
    inn       = Column(String(20))
    sozdano   = Column(DateTime, server_default=func.now())

class VidSyrya(Base):
    """Виды сырья (битум, щебень, песок, минпорошок и т.д.)"""
    __tablename__ = "vidy_syrya"
    id         = Column(Integer, primary_key=True)
    name       = Column(String(100), nullable=False)   # "Битум БНД 60/90"
    edinitsa   = Column(String(10), default="кг")      # единица измерения
    min_ostatok = Column(Float, default=0)             # минимальный остаток для предупреждения

class MarkaAsfalta(Base):
    """Марки производимого асфальта"""
    __tablename__ = "marki_asfalta"
    id   = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)          # "АБВ тип Б, крупнозернистый"
    kod  = Column(String(20))                           # "ABV-B"

class Pokupatel(Base):
    """Покупатели асфальта"""
    __tablename__ = "pokupateli"
    id       = Column(Integer, primary_key=True)
    name     = Column(String(200), nullable=False)
    telefon  = Column(String(20))
    inn      = Column(String(20))
    adres    = Column(String(300))
    sozdano  = Column(DateTime, server_default=func.now())

class Avto(Base):
    """База автомобилей"""
    __tablename__ = "avto"
    id            = Column(Integer, primary_key=True)
    gos_nomer     = Column(String(20), unique=True, nullable=False)  # "01А123АА"
    pokupatel_id  = Column(Integer, ForeignKey("pokupateli.id"), nullable=True)
    postavshik_id = Column(Integer, ForeignKey("postavshiki.id"), nullable=True)
    marka         = Column(String(100))                              # марка грузовика
    gruzopod_kg   = Column(Float)                                    # грузоподъёмность кг
    pokupatel     = relationship("Pokupatel")
    postavshik    = relationship("Postavshik")

# ─── ОПЕРАЦИИ ──────────────────────────────────────────────────

class PrikhodSyrya(Base):
    """Приход сырья через весы"""
    __tablename__ = "prikhod_syrya"
    id             = Column(Integer, primary_key=True)
    data_vremya    = Column(DateTime, server_default=func.now())
    vid_syrya_id   = Column(Integer, ForeignKey("vidy_syrya.id"), nullable=False)
    postavshik_id  = Column(Integer, ForeignKey("postavshiki.id"), nullable=False)
    avto_id        = Column(Integer, ForeignKey("avto.id"))
    nomer_nakladnoy = Column(String(50))
    brutto_kg      = Column(Float, nullable=False)   # вес с грузом
    tara_kg        = Column(Float, nullable=False)   # вес пустой машины
    netto_kg       = Column(Float, nullable=False)   # brutto - tara (считается авто)
    operator       = Column(String(100))
    primechanie    = Column(String(300))

    vid_syrya  = relationship("VidSyrya")
    postavshik = relationship("Postavshik")
    avto       = relationship("Avto")

class RaskhodSyrya(Base):
    """Расход сырья на производство"""
    __tablename__ = "raskhod_syrya"
    id              = Column(Integer, primary_key=True)
    data_vremya     = Column(DateTime, server_default=func.now())
    vid_syrya_id    = Column(Integer, ForeignKey("vidy_syrya.id"), nullable=False)
    marka_id        = Column(Integer, ForeignKey("marki_asfalta.id"), nullable=False)
    fakt_kg         = Column(Float, nullable=False)   # фактический расход с весов
    norma_kg        = Column(Float)                   # норма по рецептуре
    otklonenie_pct  = Column(Float)                   # отклонение в %
    operator        = Column(String(100))

    vid_syrya = relationship("VidSyrya")
    marka     = relationship("MarkaAsfalta")

class Proizvodstvo(Base):
    """Произведённый асфальт — каждая партия"""
    __tablename__ = "proizvodstvo"
    id           = Column(Integer, primary_key=True)
    data_vremya  = Column(DateTime, server_default=func.now())
    marka_id     = Column(Integer, ForeignKey("marki_asfalta.id"), nullable=False)
    smena        = Column(Integer, default=1)         # 1 или 2
    ves_kg       = Column(Float, nullable=False)      # вес партии с весов
    temperatura  = Column(Float)                      # температура смеси °C
    vremya_nach  = Column(String(10))                 # "10:24"
    vremya_kon   = Column(String(10))                 # "10:31"
    operator     = Column(String(100))

    marka = relationship("MarkaAsfalta")

class Prodazha(Base):
    """Продажа / отгрузка асфальта покупателю"""
    __tablename__ = "prodazhi"
    id             = Column(Integer, primary_key=True)
    data_vremya    = Column(DateTime, server_default=func.now())
    pokupatel_id   = Column(Integer, ForeignKey("pokupateli.id"), nullable=False)
    avto_id        = Column(Integer, ForeignKey("avto.id"))
    marka_id       = Column(Integer, ForeignKey("marki_asfalta.id"), nullable=False)
    brutto_kg      = Column(Float, nullable=False)
    tara_kg        = Column(Float, nullable=False)
    netto_kg       = Column(Float, nullable=False)
    tsena_za_tonnu = Column(Float)                    # цена за тонну в сумах
    summa          = Column(Float)                    # итоговая сумма
    operator       = Column(String(100))
    nakladnaya_no  = Column(String(50))

    pokupatel = relationship("Pokupatel")
    avto      = relationship("Avto")
    marka     = relationship("MarkaAsfalta")

class Ostatok(Base):
    """Текущие остатки сырья на складе (обновляются при каждой операции)"""
    __tablename__ = "ostatki"
    id           = Column(Integer, primary_key=True)
    vid_syrya_id = Column(Integer, ForeignKey("vidy_syrya.id"), unique=True, nullable=False)
    kolichestvo_kg = Column(Float, default=0)
    obnovleno    = Column(DateTime, server_default=func.now(), onupdate=func.now())

    vid_syrya = relationship("VidSyrya")
