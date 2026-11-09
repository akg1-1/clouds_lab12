from typing import Optional

import psycopg2
from fastapi import APIRouter, HTTPException, Query, status

import db.db as db
from components.schemas import (
    EquipmentCreate,
    EquipmentModelCreate,
    EquipmentModelOut,
    EquipmentOut,
    EquipmentTypeCreate,
    EquipmentTypeOut,
    EquipmentUpdate,      # ← добавить
    IdResponse,
    MaintenanceTypeOut,
    ManufacturerCreate,
    ManufacturerOut,
    StatusOut,
    EquipmentScheduleOut,
    ScheduleEventOut,
)

router = APIRouter(prefix="/api", tags=["equipment"])


# =====================================================================
# 1. ДАННЫЕ ДЛЯ ВЫПАДАЮЩИХ СПИСКОВ
# =====================================================================

@router.get("/manufacturers", response_model=list[ManufacturerOut])
def list_manufacturers():
    """Производители для <select>."""
    return db.get_manufacturers()


@router.get("/equipment-types", response_model=list[EquipmentTypeOut])
def list_equipment_types():
    """Виды оборудования."""
    return db.get_equipment_types()


@router.get("/equipment-models", response_model=list[EquipmentModelOut])
def list_equipment_models(
    equipment_type_id: Optional[int] = Query(None, description="Фильтр по виду оборудования"),
    manufacturer_id: Optional[int] = Query(None, description="Фильтр по производителю"),
):
    """Модели, при необходимости отфильтрованные — для каскадных списков."""
    return db.get_equipment_models(
        equipment_type_id=equipment_type_id,
        manufacturer_id=manufacturer_id,
    )


@router.get("/maintenance-types", response_model=list[MaintenanceTypeOut])
def list_maintenance_types():
    """Виды работ: ТО / ТР / КР."""
    return db.get_maintenance_types()


@router.get("/equipment-statuses", response_model=list[StatusOut])
def list_equipment_statuses():
    """Статусы оборудования."""
    return db.get_equipment_statuses()


# =====================================================================
# 2. РЕЕСТР ОБОРУДОВАНИЯ: ЧТЕНИЕ
# =====================================================================

@router.get("/equipments", response_model=list[EquipmentOut])
def list_equipments(
    status: Optional[str] = Query(None, description="ACTIVE / REPAIR / DECOMMISSIONED"),
    equipment_model_id: Optional[int] = Query(None, description="Фильтр по модели"),
):
    """Реестр оборудования с расшифровкой модели, типа, производителя."""
    return db.get_equipment_list(
        status=status,
        equipment_model_id=equipment_model_id,
    )


@router.get("/equipments/{equipment_id}", response_model=EquipmentOut)
def get_equipment(equipment_id: int):
    """Одна единица оборудования по id — для формы редактирования."""
    item = db.get_equipment_by_id(equipment_id)
    if not item:
        raise HTTPException(status_code=404, detail="Оборудование не найдено")
    return item


# =====================================================================
# 3. ДОБАВЛЕНИЕ НОВЫХ ЗАПИСЕЙ
# =====================================================================

@router.post("/manufacturers", response_model=IdResponse,
             status_code=status.HTTP_201_CREATED)
def create_manufacturer(payload: ManufacturerCreate):
    """Добавляет производителя. Если уже есть — вернёт его id."""
    try:
        new_id = db.add_manufacturer(
            name=payload.name,
            country=payload.country,
            contact_info=payload.contact_info,
        )
    except psycopg2.Error as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return IdResponse(id=new_id)


@router.post("/equipment-types", response_model=IdResponse,
             status_code=status.HTTP_201_CREATED)
def create_equipment_type(payload: EquipmentTypeCreate):
    """Добавляет вид оборудования."""
    try:
        new_id = db.add_equipment_type(
            name=payload.name,
            description=payload.description,
        )
    except psycopg2.Error as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return IdResponse(id=new_id)


@router.post("/equipment-models", response_model=IdResponse,
             status_code=status.HTTP_201_CREATED)
def create_equipment_model(payload: EquipmentModelCreate):
    """Добавляет модель оборудования."""
    try:
        new_id = db.add_equipment_model(
            equipment_type_id=payload.equipment_type_id,
            manufacturer_id=payload.manufacturer_id,
            name=payload.name,
            model_code=payload.model_code,
        )
    except psycopg2.Error as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return IdResponse(id=new_id)


@router.post("/equipments", response_model=IdResponse,
             status_code=status.HTTP_201_CREATED)
def create_equipment(payload: EquipmentCreate):
    """Добавляет конкретную единицу оборудования."""
    try:
        new_id = db.add_equipment(
            equipment_model_id=payload.equipment_model_id,
            inventory_no=payload.inventory_no,
            serial_no=payload.serial_no,
            commissioning_date=(
                payload.commissioning_date.isoformat()
                if payload.commissioning_date else None
            ),
            status=payload.status,
            comment=payload.comment,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except psycopg2.errors.UniqueViolation:
        raise HTTPException(
            status_code=409,
            detail=f"Оборудование с инвентарным номером '{payload.inventory_no}' уже существует",
        )
    except psycopg2.errors.ForeignKeyViolation:
        raise HTTPException(
            status_code=422,
            detail=f"Модель с id={payload.equipment_model_id} не найдена",
        )
    except psycopg2.Error as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return IdResponse(id=new_id)


# =====================================================================
# 4. ОБНОВЛЕНИЕ ОБОРУДОВАНИЯ (ПАСПОРТНЫЕ ПОЛЯ)
# =====================================================================

@router.patch("/equipments/{equipment_id}", response_model=EquipmentOut)
def update_equipment(equipment_id: int, payload: EquipmentUpdate):
    """Частичное обновление паспортных данных оборудования."""
    data = payload.model_dump(exclude_unset=True)

    if "commissioning_date" in data and data["commissioning_date"] is not None:
        data["commissioning_date"] = data["commissioning_date"].isoformat()

    try:
        updated = db.update_equipment(equipment_id, **data)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except psycopg2.errors.UniqueViolation:
        raise HTTPException(
            status_code=409,
            detail=f"Инвентарный номер '{data.get('inventory_no')}' уже занят",
        )
    except psycopg2.Error as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    if not updated:
        raise HTTPException(status_code=404, detail="Оборудование не найдено")
    return updated


# =====================================================================
# 5. РАСПИСАНИЕ ТО/ТР/КР
# =====================================================================

@router.get("/equipments/{equipment_id}/schedule",
            response_model=EquipmentScheduleOut)
def equipment_schedule(equipment_id: int, limit: int = Query(3, ge=1, le=12)):
    """Ближайшие даты ТО/ТР/КР для одной единицы оборудования."""
    data = db.get_equipment_schedule(equipment_id, limit=limit)
    if not data:
        raise HTTPException(status_code=404, detail="Оборудование не найдено")
    return data


@router.get("/schedule", response_model=list[ScheduleEventOut])
def schedule(
    horizon_days: int = Query(90, ge=1, le=730, description="Горизонт планирования в днях"),
    code: Optional[list[str]] = Query(None, description="Фильтр по видам работ: TO, TR, KR"),
):
    """Сводный календарный план-график по всему активному оборудованию."""
    return db.get_schedule_events(horizon_days=horizon_days, codes=code)