import os
import psycopg2

# --- Параметры подключения ---
DB_HOST = os.getenv("PGHOST", "localhost")
DB_PORT = os.getenv("PGPORT", "5432")
DB_NAME = os.getenv("PGDATABASE", "equipment_maintenance")
DB_USER = os.getenv("PGUSER", "postgres")
DB_PASSWORD = os.getenv("PGPASSWORD", "postgres")


MANUFACTURERS = [
    ("Siemens",             "Germany",     "support@siemens.com"),
    ("ABB",                 "Switzerland", "support@abb.com"),
    ("DMG Mori",            "Japan",       "support@dmgmori.com"),
    ("Haas",                "USA",         "support@haas.com"),
    ("Atlas Copco",         "Sweden",      "support@atlascopco.com"),
    ("Kaeser",              "Germany",     "support@kaeser.com"),
    ("Grundfos",            "Denmark",     "support@grundfos.com"),
    ("Schneider Electric",  "France",      "support@schneider.com"),
]

EQUIPMENT_TYPES = [
    ("Токарный станок",  "Металлообрабатывающее оборудование для точения"),
    ("Фрезерный станок", "Металлообрабатывающее оборудование для фрезерования"),
    ("Компрессор",       "Воздушный компрессор для пневмосистем"),
    ("Насос",            "Промышленный насос для перекачки жидкостей"),
    ("Шкаф управления",  "Электротехнический шкаф с автоматикой"),
]

MAINTENANCE_TYPES = [
    ("TO", "Технический осмотр", 1, "#4CAF50"),
    ("TR", "Технический ремонт",  2, "#FF9800"),
    ("KR", "Капитальный ремонт",  3, "#F44336"),
]

# (тип оборудования, производитель, название модели, код модели)
EQUIPMENT_MODELS = [
    ("Токарный станок",  "DMG Mori",           "CTX 310 ecoline", "CTX-310"),
    ("Токарный станок",  "Haas",               "ST-20",           "ST-20"),
    ("Фрезерный станок", "DMG Mori",           "DMU 50",          "DMU-50"),
    ("Фрезерный станок", "Haas",               "VF-2",            "VF-2"),
    ("Компрессор",       "Atlas Copco",        "GA 30",           "GA-30"),
    ("Компрессор",       "Kaeser",             "BSD 75",          "BSD-75"),
    ("Насос",            "Grundfos",           "CR 15-5",         "CR15-5"),
    ("Насос",            "Grundfos",           "NK 65-200",       "NK65-200"),
    ("Шкаф управления",  "Schneider Electric", "Prisma P",        "PRISMA-P"),
    ("Шкаф управления",  "ABB",                "MNS 3.0",         "MNS-3.0"),
]

# (код модели, код работы, интервал, единица, start_from, duration, labor)
MAINTENANCE_NORMS = [
    # CTX 310 ecoline
    ("CTX-310",   "TO", 1,   "MONTH", "LAST_SAME",     2.0,  1.5),
    ("CTX-310",   "TR", 6,   "MONTH", "LAST_SAME",     8.0,  6.0),
    ("CTX-310",   "KR", 36,  "MONTH", "COMMISSIONING", 40.0, 24.0),

    # Haas ST-20
    ("ST-20",     "TO", 1,   "MONTH", "LAST_SAME",     2.0,  1.5),
    ("ST-20",     "TR", 6,   "MONTH", "LAST_SAME",     10.0, 7.0),
    ("ST-20",     "KR", 48,  "MONTH", "COMMISSIONING", 48.0, 30.0),

    # DMU 50
    ("DMU-50",    "TO", 1,   "MONTH", "LAST_SAME",     2.5,  2.0),
    ("DMU-50",    "TR", 6,   "MONTH", "LAST_SAME",     12.0, 8.0),
    ("DMU-50",    "KR", 36,  "MONTH", "COMMISSIONING", 56.0, 36.0),

    # Haas VF-2
    ("VF-2",      "TO", 1,   "MONTH", "LAST_SAME",     2.5,  2.0),
    ("VF-2",      "TR", 6,   "MONTH", "LAST_SAME",     10.0, 7.0),
    ("VF-2",      "KR", 48,  "MONTH", "COMMISSIONING", 48.0, 30.0),

    # Atlas Copco GA 30
    ("GA-30",     "TO", 1,   "MONTH", "LAST_SAME",     1.5,  1.0),
    ("GA-30",     "TR", 12,  "MONTH", "LAST_SAME",     16.0, 10.0),
    ("GA-30",     "KR", 60,  "MONTH", "COMMISSIONING", 80.0, 48.0),

    # Kaeser BSD 75
    ("BSD-75",    "TO", 1,   "MONTH", "LAST_SAME",     1.5,  1.0),
    ("BSD-75",    "TR", 12,  "MONTH", "LAST_SAME",     20.0, 12.0),
    ("BSD-75",    "KR", 60,  "MONTH", "COMMISSIONING", 96.0, 56.0),

    # Grundfos CR 15-5
    ("CR15-5",    "TO", 3,   "MONTH", "LAST_SAME",     1.0,  0.5),
    ("CR15-5",    "TR", 12,  "MONTH", "LAST_SAME",     6.0,  4.0),
    ("CR15-5",    "KR", 60,  "MONTH", "COMMISSIONING", 32.0, 20.0),

    # Grundfos NK 65-200
    ("NK65-200",  "TO", 3,   "MONTH", "LAST_SAME",     1.0,  0.5),
    ("NK65-200",  "TR", 12,  "MONTH", "LAST_SAME",     8.0,  5.0),
    ("NK65-200",  "KR", 60,  "MONTH", "COMMISSIONING", 40.0, 24.0),

    # Schneider Prisma P
    ("PRISMA-P",  "TO", 6,   "MONTH", "LAST_SAME",     1.0,  0.5),
    ("PRISMA-P",  "TR", 24,  "MONTH", "LAST_SAME",     4.0,  3.0),
    ("PRISMA-P",  "KR", 120, "MONTH", "COMMISSIONING", 16.0, 10.0),

    # ABB MNS 3.0
    ("MNS-3.0",   "TO", 6,   "MONTH", "LAST_SAME",     1.0,  0.5),
    ("MNS-3.0",   "TR", 24,  "MONTH", "LAST_SAME",     4.0,  3.0),
    ("MNS-3.0",   "KR", 120, "MONTH", "COMMISSIONING", 16.0, 10.0),
]

# (код модели, инвентарный №, заводской №, дата ввода, статус, комментарий)
EQUIPMENTS = [
    # Токарные станки
    ("CTX-310",   "ST-001",  "SN-CTX-1001", "2019-03-15", "ACTIVE",         "Токарный участок №1"),
    ("CTX-310",   "ST-002",  "SN-CTX-1002", "2021-07-01", "ACTIVE",         "Токарный участок №1"),
    ("CTX-310",   "ST-003",  "SN-CTX-1003", "2016-05-20", "REPAIR",         "Токарный участок №2, в ремонте"),

    ("ST-20",     "ST-004",  "SN-ST20-2001", "2020-11-10", "ACTIVE",        "Токарный участок №2"),
    ("ST-20",     "ST-005",  "SN-ST20-2002", "2022-02-18", "ACTIVE",        "Токарный участок №2"),

    # Фрезерные станки
    ("DMU-50",    "FR-001",  "SN-DMU-3001", "2018-09-05", "ACTIVE",         "Фрезерный участок"),
    ("DMU-50",    "FR-002",  "SN-DMU-3002", "2023-04-12", "ACTIVE",         "Фрезерный участок"),

    ("VF-2",      "FR-003",  "SN-VF2-4001", "2017-06-30", "ACTIVE",         "Фрезерный участок"),
    ("VF-2",      "FR-004",  "SN-VF2-4002", "2015-01-22", "DECOMMISSIONED", "Списан, выведен из эксплуатации"),

    # Компрессоры
    ("GA-30",     "CM-001",  "SN-GA30-5001", "2019-10-01", "ACTIVE",        "Компрессорная, основная линия"),
    ("GA-30",     "CM-002",  "SN-GA30-5002", "2021-12-15", "ACTIVE",        "Компрессорная, резерв"),

    ("BSD-75",    "CM-003",  "SN-BSD75-6001", "2020-03-08", "ACTIVE",       "Компрессорная, цех №3"),

    # Насосы
    ("CR15-5",    "NS-001",  "SN-CR15-7001", "2022-05-20", "ACTIVE",        "Насосная станция, контур А"),
    ("CR15-5",    "NS-002",  "SN-CR15-7002", "2022-05-20", "ACTIVE",        "Насосная станция, контур Б"),

    ("NK65-200",  "NS-003",  "SN-NK65-8001", "2018-08-14", "ACTIVE",        "Насосная станция, магистраль"),
    ("NK65-200",  "NS-004",  "SN-NK65-8002", "2016-02-01", "REPAIR",        "Насосная станция, в ремонте"),

    # Шкафы управления
    ("PRISMA-P",  "SC-001",  "SN-PR-P-9001", "2020-01-10", "ACTIVE",        "Шкаф управления линией №1"),
    ("PRISMA-P",  "SC-002",  "SN-PR-P-9002", "2020-01-10", "ACTIVE",        "Шкаф управления линией №2"),

    ("MNS-3.0",   "SC-003",  "SN-MNS-9101", "2021-09-25", "ACTIVE",         "Шкаф управления подстанции"),
    ("MNS-3.0",   "SC-004",  "SN-MNS-9102", "2019-04-03", "ACTIVE",         "Шкаф управления цеха №3"),
]


def get_conn():
    return psycopg2.connect(
        host=DB_HOST, port=DB_PORT,
        dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD,
    )


def seed_manufacturers(cur):
    cur.executemany(
        "INSERT INTO manufacturer (name, country, contact_info) "
        "VALUES (%s, %s, %s) ON CONFLICT (name) DO NOTHING;",
        MANUFACTURERS,
    )
    print(f"manufacturer: добавлено/пропущено {len(MANUFACTURERS)} записей.")


def seed_equipment_types(cur):
    cur.executemany(
        "INSERT INTO equipment_type (name, description) "
        "VALUES (%s, %s) ON CONFLICT (name) DO NOTHING;",
        EQUIPMENT_TYPES,
    )
    print(f"equipment_type: добавлено/пропущено {len(EQUIPMENT_TYPES)} записей.")


def seed_maintenance_types(cur):
    cur.executemany(
        "INSERT INTO maintenance_type (code, name, level, color) "
        "VALUES (%s, %s, %s, %s) ON CONFLICT (code) DO NOTHING;",
        MAINTENANCE_TYPES,
    )
    print(f"maintenance_type: добавлено/пропущено {len(MAINTENANCE_TYPES)} записей.")


def seed_equipment_models(cur):
    for type_name, manufacturer_name, model_name, model_code in EQUIPMENT_MODELS:
        cur.execute(
            """
            INSERT INTO equipment_model
                (equipment_type_id, manufacturer_id, name, model_code)
            VALUES (
                (SELECT id FROM equipment_type WHERE name = %s),
                (SELECT id FROM manufacturer   WHERE name = %s),
                %s, %s
            )
            ON CONFLICT (manufacturer_id, model_code) DO NOTHING;
            """,
            (type_name, manufacturer_name, model_name, model_code),
        )
    print(f"equipment_model: обработано {len(EQUIPMENT_MODELS)} записей.")


def seed_maintenance_norms(cur):
    for model_code, work_code, value, unit, start_from, duration, labor in MAINTENANCE_NORMS:
        cur.execute(
            """
            INSERT INTO maintenance_norm
                (equipment_model_id, maintenance_type_id,
                 interval_value, interval_unit, start_from,
                 duration_hours, labor_norm)
            VALUES (
                (SELECT id FROM equipment_model  WHERE model_code = %s),
                (SELECT id FROM maintenance_type WHERE code = %s),
                %s, %s, %s, %s, %s
            )
            ON CONFLICT DO NOTHING;
            """,
            (model_code, work_code, value, unit, start_from, duration, labor),
        )
    print(f"maintenance_norm: обработано {len(MAINTENANCE_NORMS)} записей.")


def seed_equipments(cur):
    for model_code, inv_no, serial_no, commissioning_date, status, comment in EQUIPMENTS:
        cur.execute(
            """
            INSERT INTO equipment
                (equipment_model_id, inventory_no, serial_no,
                 commissioning_date, status, comment)
            VALUES (
                (SELECT id FROM equipment_model WHERE model_code = %s),
                %s, %s, %s, %s, %s
            )
            ON CONFLICT (inventory_no) DO NOTHING;
            """,
            (model_code, inv_no, serial_no, commissioning_date, status, comment),
        )
    print(f"equipment: обработано {len(EQUIPMENTS)} записей.")


def main() -> None:
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            seed_manufacturers(cur)
            seed_equipment_types(cur)
            seed_maintenance_types(cur)
            seed_equipment_models(cur)
            seed_maintenance_norms(cur)
            seed_equipments(cur)
        conn.commit()
        print("Данные успешно загружены.")
    except Exception as exc:
        conn.rollback()
        print(f"Ошибка при загрузке данных: {exc}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()