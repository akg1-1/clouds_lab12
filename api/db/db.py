import os
from contextlib import contextmanager
from typing import Optional

import psycopg2
from psycopg2.extras import RealDictCursor

from datetime import date, timedelta


# =====================================================================
# 1. ПОДКЛЮЧЕНИЕ К БАЗЕ ДАННЫХ
# =====================================================================

# --- Параметры подключения ---
DB_HOST = os.getenv("PGHOST", "localhost")
DB_PORT = os.getenv("PGPORT", "5432")
DB_NAME = os.getenv("PGDATABASE", "equipment_maintenance")
DB_USER = os.getenv("PGUSER", "postgres")
DB_PASSWORD = os.getenv("PGPASSWORD", "postgres")


@contextmanager
def get_cursor(commit: bool = False):
    """Контекстный менеджер: соединение + курсор с автокоммитом/откатом."""
    conn = psycopg2.connect(
        host=DB_HOST, port=DB_PORT,
        dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD,
    )
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            yield cur
        if commit:
            conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# =====================================================================
# 2. ДАННЫЕ ДЛЯ ВЫПАДАЮЩИХ СПИСКОВ
# =====================================================================

def get_manufacturers() -> list[dict]:
    """Список производителей для <select>."""
    with get_cursor() as cur:
        cur.execute("""
            SELECT id, name, country
            FROM manufacturer
            ORDER BY name;
        """)
        return cur.fetchall()


def get_equipment_types() -> list[dict]:
    """Список видов оборудования."""
    with get_cursor() as cur:
        cur.execute("""
            SELECT id, name, description
            FROM equipment_type
            ORDER BY name;
        """)
        return cur.fetchall()


def get_equipment_models(
    equipment_type_id: Optional[int] = None,
    manufacturer_id: Optional[int] = None,
) -> list[dict]:
    """
    Список моделей. Можно фильтровать по типу и/или производителю —
    удобно для каскадных списков: выбрал тип → отфильтровались модели.
    """
    sql = """
        SELECT
            em.id,
            em.name,
            em.model_code,
            em.equipment_type_id,
            em.manufacturer_id,
            et.name AS equipment_type_name,
            m.name  AS manufacturer_name
        FROM equipment_model em
        JOIN equipment_type et ON et.id = em.equipment_type_id
        JOIN manufacturer   m  ON m.id  = em.manufacturer_id
        WHERE 1 = 1
    """
    params: list = []

    if equipment_type_id is not None:
        sql += " AND em.equipment_type_id = %s"
        params.append(equipment_type_id)

    if manufacturer_id is not None:
        sql += " AND em.manufacturer_id = %s"
        params.append(manufacturer_id)

    sql += " ORDER BY et.name, m.name, em.name;"

    with get_cursor() as cur:
        cur.execute(sql, params)
        return cur.fetchall()


def get_maintenance_types() -> list[dict]:
    """Виды работ: ТО / ТР / КР."""
    with get_cursor() as cur:
        cur.execute("""
            SELECT id, code, name, level, color
            FROM maintenance_type
            ORDER BY level;
        """)
        return cur.fetchall()


def get_equipment_statuses() -> list[dict]:
    """
    Статусы оборудования — по CHECK-ограничению в таблице.
    Держим их в коде, чтобы UI не пришлось знать про CHECK.
    """
    return [
        {"code": "ACTIVE",         "name": "В эксплуатации"},
        {"code": "REPAIR",         "name": "В ремонте"},
        {"code": "DECOMMISSIONED", "name": "Списано"},
    ]


# =====================================================================
# 3. РЕЕСТР ОБОРУДОВАНИЯ: ЧТЕНИЕ
# =====================================================================

def get_equipment_list(
    status: Optional[str] = None,
    equipment_model_id: Optional[int] = None,
) -> list[dict]:
    """
    Полный список оборудования с расшифровкой модели, типа, производителя.
    Нужен для таблицы «Реестр оборудования» и для выпадающих списков
    «выберите единицу оборудования» при планировании.
    """
    sql = """
        SELECT
            e.id,
            e.inventory_no,
            e.serial_no,
            e.commissioning_date,
            e.status,
            e.comment,
            em.id   AS equipment_model_id,
            em.name AS model_name,
            em.model_code,
            et.name AS equipment_type_name,
            m.name  AS manufacturer_name
        FROM equipment e
        JOIN equipment_model em ON em.id = e.equipment_model_id
        JOIN equipment_type  et ON et.id = em.equipment_type_id
        JOIN manufacturer    m  ON m.id  = em.manufacturer_id
        WHERE 1 = 1
    """
    params: list = []

    if status is not None:
        sql += " AND e.status = %s"
        params.append(status)

    if equipment_model_id is not None:
        sql += " AND e.equipment_model_id = %s"
        params.append(equipment_model_id)

    sql += " ORDER BY et.name, em.name, e.inventory_no;"

    with get_cursor() as cur:
        cur.execute(sql, params)
        return cur.fetchall()


# =====================================================================
# 4. ДОБАВЛЕНИЕ НОВЫХ ЗАПИСЕЙ
# =====================================================================

def add_manufacturer(name: str, country: Optional[str] = None,
                     contact_info: Optional[str] = None) -> int:
    """Добавляет производителя, возвращает id. Если уже есть — возвращает существующий."""
    with get_cursor(commit=True) as cur:
        cur.execute("""
            INSERT INTO manufacturer (name, country, contact_info)
            VALUES (%s, %s, %s)
            ON CONFLICT (name) DO UPDATE
                SET country = EXCLUDED.country,
                    contact_info = EXCLUDED.contact_info
            RETURNING id;
        """, (name, country, contact_info))
        return cur.fetchone()["id"]


def add_equipment_type(name: str, description: Optional[str] = None) -> int:
    """Добавляет вид оборудования, возвращает id."""
    with get_cursor(commit=True) as cur:
        cur.execute("""
            INSERT INTO equipment_type (name, description)
            VALUES (%s, %s)
            ON CONFLICT (name) DO UPDATE
                SET description = EXCLUDED.description
            RETURNING id;
        """, (name, description))
        return cur.fetchone()["id"]


def add_equipment_model(equipment_type_id: int, manufacturer_id: int,
                        name: str, model_code: Optional[str] = None) -> int:
    """
    Добавляет модель. Модель — это «тип оборудования от производителя»,
    на неё потом ссылаются и нормативы, и конкретные единицы.
    """
    with get_cursor(commit=True) as cur:
        cur.execute("""
            INSERT INTO equipment_model
                (equipment_type_id, manufacturer_id, name, model_code)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (manufacturer_id, model_code) DO UPDATE
                SET name = EXCLUDED.name,
                    equipment_type_id = EXCLUDED.equipment_type_id
            RETURNING id;
        """, (equipment_type_id, manufacturer_id, name, model_code))
        return cur.fetchone()["id"]


def add_equipment(
    equipment_model_id: int,
    inventory_no: str,
    serial_no: Optional[str] = None,
    commissioning_date: Optional[str] = None,
    status: str = "ACTIVE",
    comment: Optional[str] = None,
) -> int:
    """
    Добавляет конкретную единицу оборудования.
    commissioning_date — строка 'YYYY-MM-DD' или None.
    Возвращает id новой записи.
    """
    if status not in ("ACTIVE", "REPAIR", "DECOMMISSIONED"):
        raise ValueError(f"Недопустимый статус: {status}")

    with get_cursor(commit=True) as cur:
        cur.execute("""
            INSERT INTO equipment
                (equipment_model_id, inventory_no, serial_no,
                 commissioning_date, status, comment)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id;
        """, (
            equipment_model_id, inventory_no, serial_no,
            commissioning_date, status, comment,
        ))
        return cur.fetchone()["id"]


def add_equipment_with_model(
    *,
    inventory_no: str,
    equipment_model_id: int,
    serial_no: Optional[str] = None,
    commissioning_date: Optional[str] = None,
    status: str = "ACTIVE",
    comment: Optional[str] = None,
) -> int:
    """
    Обёртка для самого частого сценария — добавление станка,
    когда модель уже выбрана в выпадающем списке.
    Отдельная функция, чтобы UI-слой не тянул детали.
    """
    return add_equipment(
        equipment_model_id=equipment_model_id,
        inventory_no=inventory_no,
        serial_no=serial_no,
        commissioning_date=commissioning_date,
        status=status,
        comment=comment,
    )


# =====================================================================
# 5. ОБОРУДОВАНИЕ: ПОЛУЧЕНИЕ И ОБНОВЛЕНИЕ ПО ID
# =====================================================================

def get_equipment_by_id(equipment_id: int) -> Optional[dict]:
    """Одна единица оборудования с расшифровкой модели, типа, производителя."""
    with get_cursor() as cur:
        cur.execute("""
            SELECT
                e.id,
                e.inventory_no,
                e.serial_no,
                e.commissioning_date,
                e.status,
                e.comment,
                em.id   AS equipment_model_id,
                em.name AS model_name,
                em.model_code,
                et.id   AS equipment_type_id,
                et.name AS equipment_type_name,
                m.id    AS manufacturer_id,
                m.name  AS manufacturer_name
            FROM equipment e
            JOIN equipment_model em ON em.id = e.equipment_model_id
            JOIN equipment_type  et ON et.id = em.equipment_type_id
            JOIN manufacturer    m  ON m.id  = em.manufacturer_id
            WHERE e.id = %s;
        """, (equipment_id,))
        return cur.fetchone()


def update_equipment(
    equipment_id: int,
    *,
    inventory_no: Optional[str] = None,
    serial_no: Optional[str] = None,
    commissioning_date: Optional[str] = None,
    status: Optional[str] = None,
    comment: Optional[str] = None,
) -> Optional[dict]:
    """
    Частичное обновление. Меняются только переданные поля (не None).
    Тип, производитель и модель не редактируются.
    Возвращает обновлённую запись или None, если такой id нет.
    """
    fields = []
    params: list = []

    if inventory_no is not None:
        fields.append("inventory_no = %s")
        params.append(inventory_no)
    if serial_no is not None:
        fields.append("serial_no = %s")
        params.append(serial_no)
    if commissioning_date is not None:
        fields.append("commissioning_date = %s")
        params.append(commissioning_date)
    if status is not None:
        if status not in ("ACTIVE", "REPAIR", "DECOMMISSIONED"):
            raise ValueError(f"Недопустимый статус: {status}")
        fields.append("status = %s")
        params.append(status)
    if comment is not None:
        fields.append("comment = %s")
        params.append(comment)

    if not fields:
        return get_equipment_by_id(equipment_id)

    params.append(equipment_id)

    with get_cursor(commit=True) as cur:
        cur.execute(
            f"UPDATE equipment SET {', '.join(fields)} WHERE id = %s RETURNING id;",
            params,
        )
        if not cur.fetchone():
            return None

    return get_equipment_by_id(equipment_id)


# =====================================================================
# 6. РАСПИСАНИЕ ТО/ТР/КР: ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# =====================================================================

def _add_interval(base: date, value: int, unit: str) -> date:
    """Прибавляет интервал к дате. Умеет DAY / MONTH / YEAR."""
    if unit == "DAY":
        return base + timedelta(days=value)

    if unit == "MONTH":
        month_index = base.month - 1 + value
        year = base.year + month_index // 12
        month = month_index % 12 + 1
        # аккуратно с последним днём месяца
        last_day = [31, 29 if (year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)) else 28,
                    31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month - 1]
        return date(year, month, min(base.day, last_day))

    if unit == "YEAR":
        try:
            return base.replace(year=base.year + value)
        except ValueError:  # 29 февраля
            return base.replace(year=base.year + value, day=28)

    raise ValueError(f"Неизвестная единица интервала: {unit}")


def _upcoming_dates(base: date, value: int, unit: str,
                    today: date, count: int) -> list[date]:
    """Следующие count дат, начиная строго после today."""
    current = base
    safety = 0
    while current <= today and safety < 2000:
        current = _add_interval(current, value, unit)
        safety += 1

    result = []
    for _ in range(count):
        result.append(current)
        current = _add_interval(current, value, unit)
    return result


# =====================================================================
# 7. РАСПИСАНИЕ ТО/ТР/КР: ОСНОВНЫЕ ФУНКЦИИ
# =====================================================================

def get_equipment_schedule(equipment_id: int, limit: int = 3) -> Optional[dict]:
    """Расписание ТО/ТР/КР для одной единицы оборудования."""
    with get_cursor() as cur:
        cur.execute("""
            SELECT e.id, e.inventory_no, e.commissioning_date, e.status,
                   em.id AS model_id, em.name AS model_name
            FROM equipment e
            JOIN equipment_model em ON em.id = e.equipment_model_id
            WHERE e.id = %s;
        """, (equipment_id,))
        eq = cur.fetchone()
        if not eq:
            return None

        cur.execute("""
            SELECT mn.interval_value, mn.interval_unit, mn.start_from,
                   mt.code, mt.name, mt.level, mt.color
            FROM maintenance_norm mn
            JOIN maintenance_type mt ON mt.id = mn.maintenance_type_id
            WHERE mn.equipment_model_id = %s
            ORDER BY mt.level;
        """, (eq["model_id"],))
        norms = cur.fetchall()

    today = date.today()
    base = eq["commissioning_date"] or today

    schedule = []
    for n in norms:
        dates = _upcoming_dates(base, n["interval_value"], n["interval_unit"], today, limit)
        schedule.append({
            "code": n["code"],
            "name": n["name"],
            "level": n["level"],
            "color": n["color"],
            "interval_value": n["interval_value"],
            "interval_unit": n["interval_unit"],
            "next_dates": [d.isoformat() for d in dates],
        })

    return {
        "equipment_id": eq["id"],
        "inventory_no": eq["inventory_no"],
        "model_name": eq["model_name"],
        "commissioning_date": eq["commissioning_date"],
        "schedule": schedule,
    }


def get_schedule_events(horizon_days: int = 90,
                        codes: Optional[list[str]] = None) -> list[dict]:
    """
    Плоский список событий ТО/ТР/КР по всему парку активного оборудования
    на горизонт horizon_days вперёд. Готов для календарного план-графика.
    """
    with get_cursor() as cur:
        cur.execute("""
            SELECT e.id, e.inventory_no, e.commissioning_date,
                   em.id AS model_id, em.name AS model_name,
                   et.name AS type_name, m.name AS manufacturer_name
            FROM equipment e
            JOIN equipment_model em ON em.id = e.equipment_model_id
            JOIN equipment_type  et ON et.id = em.equipment_type_id
            JOIN manufacturer    m  ON m.id  = em.manufacturer_id
            WHERE e.status = 'ACTIVE';
        """)
        equipments = cur.fetchall()

        sql = """
            SELECT mn.equipment_model_id, mn.interval_value, mn.interval_unit,
                   mt.code, mt.name, mt.level, mt.color
            FROM maintenance_norm mn
            JOIN maintenance_type mt ON mt.id = mn.maintenance_type_id
        """
        params: list = []
        if codes:
            sql += " WHERE mt.code = ANY(%s)"
            params.append(codes)

        cur.execute(sql, params)
        all_norms = cur.fetchall()

    norms_by_model: dict[int, list] = {}
    for n in all_norms:
        norms_by_model.setdefault(n["equipment_model_id"], []).append(n)

    today = date.today()
    horizon_end = today + timedelta(days=horizon_days)
    events: list[dict] = []

    for eq in equipments:
        base = eq["commissioning_date"] or today
        for n in norms_by_model.get(eq["model_id"], []):
            d = base
            safety = 0
            while d <= horizon_end and safety < 5000:
                safety += 1
                if d >= today:
                    events.append({
                        "date": d.isoformat(),
                        "equipment_id": eq["id"],
                        "inventory_no": eq["inventory_no"],
                        "model_name": eq["model_name"],
                        "type_name": eq["type_name"],
                        "manufacturer_name": eq["manufacturer_name"],
                        "code": n["code"],
                        "name": n["name"],
                        "level": n["level"],
                        "color": n["color"],
                    })
                d = _add_interval(d, n["interval_value"], n["interval_unit"])

    events.sort(key=lambda x: (x["date"], x["level"], x["inventory_no"]))
    return events