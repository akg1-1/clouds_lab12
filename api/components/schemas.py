from datetime import date
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


# =====================================================================
# 1. СПРАВОЧНИКИ: СХЕМЫ ОТВЕТОВ
# =====================================================================

class ManufacturerOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    country: Optional[str] = None
    contact_info: Optional[str] = None


class EquipmentTypeOut(BaseModel):
    id: int
    name: str
    description: Optional[str] = None


class EquipmentModelOut(BaseModel):
    id: int
    name: str
    model_code: Optional[str] = None
    equipment_type_id: int
    manufacturer_id: int
    equipment_type_name: str
    manufacturer_name: str


class MaintenanceTypeOut(BaseModel):
    id: int
    code: str
    name: str
    level: int
    color: Optional[str] = None


class StatusOut(BaseModel):
    code: str
    name: str


# =====================================================================
# 2. ОБОРУДОВАНИЕ: СХЕМЫ ОТВЕТОВ
# =====================================================================

class EquipmentOut(BaseModel):
    id: int
    inventory_no: str
    serial_no: Optional[str] = None
    commissioning_date: Optional[date] = None
    status: str
    comment: Optional[str] = None
    equipment_model_id: int
    model_name: str
    model_code: Optional[str] = None
    equipment_type_name: str
    manufacturer_name: str


# =====================================================================
# 3. СОЗДАНИЕ ЗАПИСЕЙ: СХЕМЫ ЗАПРОСОВ
# =====================================================================

class ManufacturerCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    country: Optional[str] = Field(None, max_length=100)
    contact_info: Optional[str] = None


class EquipmentTypeCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None


class EquipmentModelCreate(BaseModel):
    equipment_type_id: int
    manufacturer_id: int
    name: str = Field(..., min_length=1, max_length=255)
    model_code: Optional[str] = Field(None, max_length=100)


class EquipmentCreate(BaseModel):
    equipment_model_id: int
    inventory_no: str = Field(..., min_length=1, max_length=50)
    serial_no: Optional[str] = Field(None, max_length=100)
    commissioning_date: Optional[date] = None
    status: str = Field("ACTIVE", pattern="^(ACTIVE|REPAIR|DECOMMISSIONED)$")
    comment: Optional[str] = None


# =====================================================================
# 4. ОБНОВЛЕНИЕ И СЛУЖЕБНЫЕ ОТВЕТЫ
# =====================================================================

class IdResponse(BaseModel):
    id: int


class EquipmentUpdate(BaseModel):
    """
    PATCH-семантика. Редактируются только «паспортные» поля,
    тип/производитель/модель — нет.
    """
    inventory_no: Optional[str] = Field(None, min_length=1, max_length=50)
    serial_no: Optional[str] = Field(None, max_length=100)
    commissioning_date: Optional[date] = None
    status: Optional[str] = Field(None, pattern="^(ACTIVE|REPAIR|DECOMMISSIONED)$")
    comment: Optional[str] = None


# =====================================================================
# 5. РАСПИСАНИЕ ТО/ТР/КР: СХЕМЫ ОТВЕТОВ
# =====================================================================

class MaintenanceDateOut(BaseModel):
    code: str
    name: str
    level: int
    color: Optional[str] = None
    interval_value: int
    interval_unit: str
    next_dates: list[date]


class EquipmentScheduleOut(BaseModel):
    equipment_id: int
    inventory_no: str
    model_name: str
    commissioning_date: Optional[date] = None
    schedule: list[MaintenanceDateOut]


class ScheduleEventOut(BaseModel):
    date: date
    equipment_id: int
    inventory_no: str
    model_name: str
    type_name: str
    manufacturer_name: str
    code: str
    name: str
    level: int
    color: Optional[str] = None