from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

# ─── ПРИХОД СЫРЬЯ ───────────────────────────────────────────────

class PrikhodCreate(BaseModel):
    vid_syrya_id:    int
    postavshik_id:   int
    avto_id:         Optional[int] = None
    nomer_nakladnoy: Optional[str] = None
    brutto_kg:       float = Field(gt=0)
    tara_kg:         float = Field(gt=0)
    operator:        Optional[str] = None
    primechanie:     Optional[str] = None

class PrikhodOut(BaseModel):
    id:             int
    data_vremya:    datetime
    vid_syrya_id:   int
    postavshik_id:  int
    avto_id:        Optional[int]
    brutto_kg:      float
    tara_kg:        float
    netto_kg:       float
    nomer_nakladnoy: Optional[str]
    operator:       Optional[str]

    class Config:
        from_attributes = True

# ─── РАСХОД СЫРЬЯ ───────────────────────────────────────────────

class RaskhodCreate(BaseModel):
    vid_syrya_id: int
    marka_id:     int
    fakt_kg:      float = Field(gt=0)
    norma_kg:     Optional[float] = None
    operator:     Optional[str] = None

class RaskhodOut(BaseModel):
    id:             int
    data_vremya:    datetime
    vid_syrya_id:   int
    marka_id:       int
    fakt_kg:        float
    norma_kg:       Optional[float]
    otklonenie_pct: Optional[float]
    operator:       Optional[str]

    class Config:
        from_attributes = True

# ─── ПРОИЗВОДСТВО ───────────────────────────────────────────────

class ProizvodstvoCreate(BaseModel):
    marka_id:    int
    smena:       int = Field(default=1, ge=1, le=2)
    ves_kg:      float = Field(gt=0)
    temperatura: Optional[float] = None
    vremya_nach: Optional[str] = None
    vremya_kon:  Optional[str] = None
    operator:    Optional[str] = None

class ProizvodstvoOut(BaseModel):
    id:          int
    data_vremya: datetime
    marka_id:    int
    smena:       int
    ves_kg:      float
    temperatura: Optional[float]
    vremya_nach: Optional[str]
    vremya_kon:  Optional[str]
    operator:    Optional[str]

    class Config:
        from_attributes = True

# ─── ПРОДАЖИ ────────────────────────────────────────────────────

class ProdazhaCreate(BaseModel):
    pokupatel_id:   int
    avto_id:        Optional[int] = None
    marka_id:       int
    brutto_kg:      float = Field(gt=0)
    tara_kg:        float = Field(gt=0)
    tsena_za_tonnu: Optional[float] = None
    operator:       Optional[str] = None
    nakladnaya_no:  Optional[str] = None

class ProdazhaOut(BaseModel):
    id:             int
    data_vremya:    datetime
    pokupatel_id:   int
    avto_id:        Optional[int]
    marka_id:       int
    brutto_kg:      float
    tara_kg:        float
    netto_kg:       float
    tsena_za_tonnu: Optional[float]
    summa:          Optional[float]
    operator:       Optional[str]
    nakladnaya_no:  Optional[str]

    class Config:
        from_attributes = True

# ─── СКЛАД / ОСТАТКИ ────────────────────────────────────────────

class OstatolOut(BaseModel):
    id:             int
    vid_syrya_id:   int
    kolichestvo_kg: float
    obnovleno:      datetime

    class Config:
        from_attributes = True

# ─── ДАШБОРД ────────────────────────────────────────────────────

class DashboardStats(BaseModel):
    prikhod_kg:     float
    prikhod_mashin: int
    proizvod_kg:    float
    otgruzheno_kg:  float
    vyruchka_sum:   float
    pokupatelei:    int
