// ============================================================
// 1. НАСТРОЙКИ И АДРЕСА API
// ============================================================

const API_BASE = "http://api-lab:8000";

const api = {
    manufacturers: `${API_BASE}/api/manufacturers`,
    equipmentTypes: `${API_BASE}/api/equipment-types`,
    equipmentModels: `${API_BASE}/api/equipment-models`,
    maintenanceTypes: `${API_BASE}/api/maintenance-types`,
    equipmentStatuses: `${API_BASE}/api/equipment-statuses`,
    equipments: `${API_BASE}/api/equipments`,
    schedule: `${API_BASE}/api/schedule`,
};


// ============================================================
// 2. УТИЛИТЫ
// ============================================================

async function fetchJson(url, options = {}) {
    const response = await fetch(url, {
        headers: { "Content-Type": "application/json" },
        ...options,
    });

    let data = null;
    const text = await response.text();
    if (text) {
        try { data = JSON.parse(text); } catch { data = text; }
    }

    if (!response.ok) {
        const message =
            (data && (data.detail || data.message)) ||
            `Ошибка ${response.status}`;
        throw new Error(typeof message === "string" ? message : JSON.stringify(message));
    }
    return data;
}

function el(id) {
    return document.getElementById(id);
}

function clearSelect(select, placeholder) {
    select.innerHTML = "";
    const opt = document.createElement("option");
    opt.value = "";
    opt.textContent = placeholder;
    select.appendChild(opt);
}

function fillSelect(select, items, placeholder, getValue, getLabel) {
    clearSelect(select, placeholder);
    for (const item of items) {
        const opt = document.createElement("option");
        opt.value = getValue(item);
        opt.textContent = getLabel(item);
        select.appendChild(opt);
    }
}

function showMessage(container, text, type = "success") {
    container.hidden = false;
    container.className = `message message--${type}`;
    container.textContent = text;
    if (type === "success") {
        setTimeout(() => {
            container.hidden = true;
        }, 4000);
    }
}

function formatDate(value) {
    if (!value) return "—";
    const d = new Date(value);
    if (isNaN(d)) return value;
    return d.toLocaleDateString("ru-RU");
}

const STATUS_LABELS = {
    ACTIVE: "В эксплуатации",
    REPAIR: "В ремонте",
    DECOMMISSIONED: "Списано",
};

const STATUS_CLASSES = {
    ACTIVE: "badge--active",
    REPAIR: "badge--repair",
    DECOMMISSIONED: "badge--decommissioned",
};


// ============================================================
// 3. ПЕРЕКЛЮЧЕНИЕ ВКЛАДОК
// ============================================================

document.querySelectorAll(".nav__btn").forEach(btn => {
    btn.addEventListener("click", () => {
        document.querySelectorAll(".nav__btn").forEach(b => b.classList.remove("is-active"));
        document.querySelectorAll(".tab").forEach(t => t.classList.remove("is-active"));
        btn.classList.add("is-active");
        el(`tab-${btn.dataset.tab}`).classList.add("is-active");

        // При переходе на вкладку плана-графика — обновляем данные
        if (btn.dataset.tab === "schedule") {
            loadSchedule();
        }
    });
});


// ============================================================
// 4. ЗАГРУЗКА СПРАВОЧНИКОВ
// ============================================================

async function loadStatuses() {
    const statuses = await fetchJson(api.equipmentStatuses);

    const filter = el("filter-status");
    if (filter) {
        clearSelect(filter, "Все");
        for (const s of statuses) {
            const opt = document.createElement("option");
            opt.value = s.code;
            opt.textContent = s.name;
            filter.appendChild(opt);
        }
    }

    const addStatus = el("add-status");
    if (addStatus) {
        addStatus.innerHTML = "";
        for (const s of statuses) {
            const opt = document.createElement("option");
            opt.value = s.code;
            opt.textContent = s.name;
            if (s.code === "ACTIVE") opt.selected = true;
            addStatus.appendChild(opt);
        }
    }
}

async function loadTypes() {
    const types = await fetchJson(api.equipmentTypes);

    const filter = el("filter-type");
    if (filter) {
        clearSelect(filter, "Все");
        for (const t of types) {
            const opt = document.createElement("option");
            opt.value = t.id;
            opt.textContent = t.name;
            filter.appendChild(opt);
        }
    }

    const addType = el("add-type");
    if (addType) fillSelect(addType, types, "— выберите —", t => t.id, t => t.name);

    const quick = document.querySelector('#quick-model-form select[name="equipment_type_id"]');
    if (quick) fillSelect(quick, types, "Тип *", t => t.id, t => t.name);
}

async function loadManufacturers() {
    const items = await fetchJson(api.manufacturers);

    const filter = el("filter-manufacturer");
    if (filter) {
        clearSelect(filter, "Все");
        for (const m of items) {
            const opt = document.createElement("option");
            opt.value = m.id;
            opt.textContent = m.name;
            filter.appendChild(opt);
        }
    }

    const addMfr = el("add-manufacturer");
    if (addMfr) fillSelect(addMfr, items, "— выберите —", m => m.id, m => m.name);

    const quick = document.querySelector('#quick-model-form select[name="manufacturer_id"]');
    if (quick) fillSelect(quick, items, "Производитель *", m => m.id, m => m.name);
}

async function loadModelsForFilter() {
    const models = await fetchJson(api.equipmentModels);
    const filter = el("filter-model");
    if (!filter) return;
    clearSelect(filter, "Все");
    for (const m of models) {
        const opt = document.createElement("option");
        opt.value = m.id;
        opt.textContent = `${m.model_code || m.name} · ${m.manufacturer_name}`;
        filter.appendChild(opt);
    }
}

async function loadModelsForForm() {
    const typeId = el("add-type").value;
    const manufacturerId = el("add-manufacturer").value;
    const select = el("add-model");

    if (!typeId || !manufacturerId) {
        clearSelect(select, "— сначала выберите тип и производителя —");
        return;
    }

    const params = new URLSearchParams({
        equipment_type_id: typeId,
        manufacturer_id: manufacturerId,
    });

    const models = await fetchJson(`${api.equipmentModels}?${params}`);

    if (models.length === 0) {
        clearSelect(select, "— нет моделей для этого сочетания —");
        return;
    }

    clearSelect(select, "— выберите модель —");
    for (const m of models) {
        const opt = document.createElement("option");
        opt.value = m.id;
        opt.textContent = m.name + (m.model_code ? ` (${m.model_code})` : "");
        select.appendChild(opt);
    }
}


// ============================================================
// 5. РЕЕСТР ОБОРУДОВАНИЯ (СПИСОК + ТАБЛИЦА)
// ============================================================

async function loadEquipmentList() {
    const tbody = el("equipment-tbody");
    const info = el("list-info");
    if (!tbody) return;

    tbody.innerHTML = `<tr><td colspan="8" class="empty">Загрузка…</td></tr>`;

    const params = new URLSearchParams();
    const status = el("filter-status")?.value;
    if (status) params.append("status", status);

    const modelId = el("filter-model")?.value;
    if (modelId) params.append("equipment_model_id", modelId);

    try {
        const items = await fetchJson(`${api.equipments}?${params}`);

        const typeName = el("filter-type")?.selectedOptions[0]?.textContent || "";
        const mfrName = el("filter-manufacturer")?.selectedOptions[0]?.textContent || "";
        const typeId = el("filter-type")?.value;
        const mfrId = el("filter-manufacturer")?.value;

        let filtered = items;
        if (typeId) filtered = filtered.filter(it => it.equipment_type_name === typeName);
        if (mfrId) filtered = filtered.filter(it => it.manufacturer_name === mfrName);

        renderEquipmentTable(filtered, tbody);
        if (info) info.textContent = `Показано: ${filtered.length} из ${items.length}`;
    } catch (err) {
        tbody.innerHTML = `<tr><td colspan="8" class="empty">Ошибка загрузки: ${err.message}</td></tr>`;
        if (info) info.textContent = "";
    }
}

function renderEquipmentTable(items, tbody) {
    if (!items.length) {
        tbody.innerHTML = `<tr><td colspan="8" class="empty">Нет данных</td></tr>`;
        return;
    }

    tbody.innerHTML = "";
    for (const e of items) {
        const tr = document.createElement("tr");
        tr.dataset.id = e.id;
        tr.title = "Кликните, чтобы редактировать";

        tr.innerHTML = `
            <td><strong>${e.inventory_no}</strong></td>
            <td>${e.equipment_type_name}</td>
            <td>${e.manufacturer_name}</td>
            <td>${e.model_name}${e.model_code ? ` <span class="muted">(${e.model_code})</span>` : ""}</td>
            <td>${e.serial_no || "—"}</td>
            <td>${formatDate(e.commissioning_date)}</td>
            <td>
                <span class="badge ${STATUS_CLASSES[e.status] || ""}">
                    ${STATUS_LABELS[e.status] || e.status}
                </span>
            </td>
            <td>${e.comment || "—"}</td>
        `;
        tbody.appendChild(tr);
    }

    attachRowClickHandlers();
}


// ============================================================
// 6. ФОРМА ДОБАВЛЕНИЯ ОБОРУДОВАНИЯ
// ============================================================

el("add-type").addEventListener("change", loadModelsForForm);
el("add-manufacturer").addEventListener("change", loadModelsForForm);

el("equipment-form").addEventListener("submit", async event => {
    event.preventDefault();
    const message = el("form-message");
    message.hidden = true;

    const payload = {
        equipment_model_id: Number(el("add-model").value),
        inventory_no: el("add-inventory").value.trim(),
        serial_no: el("add-serial").value.trim() || null,
        commissioning_date: el("add-date").value || null,
        status: el("add-status").value,
        comment: el("add-comment").value.trim() || null,
    };

    if (!payload.equipment_model_id) {
        showMessage(message, "Выберите модель", "error");
        return;
    }

    try {
        const result = await fetchJson(api.equipments, {
            method: "POST",
            body: JSON.stringify(payload),
        });
        showMessage(message,
            `Оборудование добавлено. id = ${result.id}. Инв. № ${payload.inventory_no}.`,
            "success");

        el("equipment-form").reset();
        clearSelect(el("add-model"), "— сначала выберите тип и производителя —");
        await loadModelsForFilter();
        await loadEquipmentList();
    } catch (err) {
        showMessage(message, `Не удалось сохранить: ${err.message}`, "error");
    }
});

el("refresh-btn").addEventListener("click", () => loadEquipmentList());

["filter-status", "filter-type", "filter-manufacturer", "filter-model"]
    .forEach(id => {
        const node = el(id);
        if (node) node.addEventListener("change", loadEquipmentList);
    });


// ============================================================
// 7. БЫСТРЫЕ ФОРМЫ СПРАВОЧНИКОВ
// ============================================================

el("quick-type-form").addEventListener("submit", async event => {
    event.preventDefault();
    const form = event.target;
    const data = Object.fromEntries(new FormData(form).entries());

    try {
        await fetchJson(api.equipmentTypes, {
            method: "POST",
            body: JSON.stringify({
                name: data.name,
                description: data.description || null,
            }),
        });
        form.reset();
        await loadTypes();
        await loadModelsForFilter();
        await loadEquipmentList();
    } catch (err) {
        alert(`Ошибка: ${err.message}`);
    }
});

el("quick-manufacturer-form").addEventListener("submit", async event => {
    event.preventDefault();
    const form = event.target;
    const data = Object.fromEntries(new FormData(form).entries());

    try {
        await fetchJson(api.manufacturers, {
            method: "POST",
            body: JSON.stringify({
                name: data.name,
                country: data.country || null,
                contact_info: data.contact_info || null,
            }),
        });
        form.reset();
        await loadManufacturers();
        await loadModelsForFilter();
        await loadEquipmentList();
    } catch (err) {
        alert(`Ошибка: ${err.message}`);
    }
});

el("quick-model-form").addEventListener("submit", async event => {
    event.preventDefault();
    const form = event.target;
    const data = Object.fromEntries(new FormData(form).entries());

    try {
        await fetchJson(api.equipmentModels, {
            method: "POST",
            body: JSON.stringify({
                equipment_type_id: Number(data.equipment_type_id),
                manufacturer_id: Number(data.manufacturer_id),
                name: data.name,
                model_code: data.model_code || null,
            }),
        });
        form.reset();
        await loadModelsForFilter();
        await loadModelsForForm();
        await loadEquipmentList();
    } catch (err) {
        alert(`Ошибка: ${err.message}`);
    }
});


// ============================================================
// 8. РЕДАКТИРОВАНИЕ ОБОРУДОВАНИЯ (МОДАЛЬНОЕ ОКНО)
// ============================================================

const editModal = el("edit-modal");

function openEditModal() {
    editModal.hidden = false;
    document.body.classList.add("modal-open");
}

function closeEditModal() {
    editModal.hidden = true;
    document.body.classList.remove("modal-open");
    const msg = el("edit-message");
    if (msg) msg.hidden = true;
}

document.querySelectorAll("#edit-modal [data-close]").forEach(node => {
    node.addEventListener("click", event => {
        event.preventDefault();
        event.stopPropagation();
        closeEditModal();
    });
});

document.addEventListener("keydown", event => {
    if (event.key === "Escape" && !editModal.hidden) {
        closeEditModal();
    }
});

async function ensureEditStatuses() {
    const select = el("edit-status");
    if (select.options.length > 0) return;

    const statuses = await fetchJson(api.equipmentStatuses);
    for (const s of statuses) {
        const opt = document.createElement("option");
        opt.value = s.code;
        opt.textContent = s.name;
        select.appendChild(opt);
    }
}

function renderEditSchedule(data) {
    const box = el("edit-schedule");
    if (!box) return;

    if (!data || !data.schedule || !data.schedule.length) {
        box.innerHTML = `<span class="muted">Для модели не заданы нормативы</span>`;
        return;
    }

    box.innerHTML = "";
    const row = document.createElement("div");
    row.className = "schedule-row";

    for (const s of data.schedule) {
        const next = s.next_dates && s.next_dates[0];
        const item = document.createElement("span");
        item.className = "schedule-item";
        item.innerHTML = `<strong>${s.code}</strong> ${next ? formatDate(next) : "—"}`;
        row.appendChild(item);
    }
    box.appendChild(row);
}

async function openEditFor(equipmentId) {
    try {
        await ensureEditStatuses();

        const item = await fetchJson(`${api.equipments}/${equipmentId}`);

        el("edit-id").value = item.id;
        el("edit-static-model").textContent =
            `${item.equipment_type_name} · ${item.manufacturer_name} · ${item.model_name}` +
            (item.model_code ? ` (${item.model_code})` : "");

        el("edit-inventory").value = item.inventory_no || "";
        el("edit-serial").value = item.serial_no || "";
        el("edit-date").value = item.commissioning_date
            ? item.commissioning_date.slice(0, 10)
            : "";
        el("edit-status").value = item.status;
        el("edit-comment").value = item.comment || "";

        // Загружаем расписание ТО/ТР/КР
        el("edit-schedule").innerHTML = `<span class="muted">Загрузка…</span>`;
        try {
            const sched = await fetchJson(`${api.equipments}/${equipmentId}/schedule`);
            renderEditSchedule(sched);
        } catch (err) {
            el("edit-schedule").innerHTML =
                `<span class="muted">Не удалось загрузить расписание: ${err.message}</span>`;
        }

        el("edit-message").hidden = true;
        openEditModal();
    } catch (err) {
        alert(`Не удалось открыть карточку: ${err.message}`);
    }
}

function attachRowClickHandlers() {
    document.querySelectorAll("#equipment-tbody tr[data-id]").forEach(tr => {
        tr.addEventListener("click", () => openEditFor(Number(tr.dataset.id)));
    });
}

el("edit-form").addEventListener("submit", async event => {
    event.preventDefault();
    const message = el("edit-message");
    message.hidden = true;

    const id = Number(el("edit-id").value);
    const payload = {
        inventory_no: el("edit-inventory").value.trim(),
        serial_no: el("edit-serial").value.trim() || null,
        commissioning_date: el("edit-date").value || null,
        status: el("edit-status").value,
        comment: el("edit-comment").value.trim() || null,
    };

    try {
        await fetchJson(`${api.equipments}/${id}`, {
            method: "PATCH",
            body: JSON.stringify(payload),
        });
        showMessage(message, "Изменения сохранены.", "success");
        await loadEquipmentList();
        setTimeout(closeEditModal, 600);
    } catch (err) {
        showMessage(message, `Не удалось сохранить: ${err.message}`, "error");
    }
});


// ============================================================
// 9. ПЛАН-ГРАФИК ТО/ТР/КР: ТАБЛИЦА И КАЛЕНДАРЬ
// ============================================================

let scheduleCache = [];                         // последние загруженные события
let calendarMonth = new Date();                 // отображаемый месяц
let currentScheduleView = "table";              // "table" | "calendar"

const MONTH_NAMES = [
    "январь", "февраль", "март", "апрель", "май", "июнь",
    "июль", "август", "сентябрь", "октябрь", "ноябрь", "декабрь",
];

function getSelectedCodes() {
    return Array.from(document.querySelectorAll('#sched-codes input:checked'))
        .map(cb => cb.value);
}

async function loadSchedule() {
    const tbody = el("schedule-tbody");
    const info = el("schedule-info");
    if (!tbody) return;

    if (currentScheduleView === "table") {
        tbody.innerHTML = `<tr><td colspan="6" class="empty">Загрузка…</td></tr>`;
    }

    const params = new URLSearchParams();

    // Если открыт календарь — расширяем горизонт так, чтобы он покрывал
    // конец отображаемого месяца. Иначе события на дальней сетке будут пустыми.
    let horizon = Number(el("sched-horizon").value);
    if (currentScheduleView === "calendar") {
        const endOfMonth = new Date(
            calendarMonth.getFullYear(),
            calendarMonth.getMonth() + 1,
            0
        );
        const today = new Date();
        today.setHours(0, 0, 0, 0);
        const daysToEnd = Math.ceil((endOfMonth - today) / 86400000) + 1;
        horizon = Math.max(horizon, daysToEnd, 1);
    }

    params.append("horizon_days", horizon);
    for (const code of getSelectedCodes()) {
        params.append("code", code);
    }

    try {
        const events = await fetchJson(`${api.schedule}?${params}`);
        scheduleCache = events;

        if (currentScheduleView === "table") {
            renderScheduleTable(events, tbody);
        } else {
            renderCalendar();
        }
        if (info) info.textContent = `Найдено событий: ${events.length}`;
    } catch (err) {
        if (currentScheduleView === "table") {
            tbody.innerHTML =
                `<tr><td colspan="6" class="empty">Ошибка: ${err.message}</td></tr>`;
        } else {
            el("calendar-grid").innerHTML =
                `<div class="empty" style="grid-column: 1 / -1;">Ошибка: ${err.message}</div>`;
        }
        if (info) info.textContent = "";
    }
}

function renderScheduleTable(events, tbody) {
    if (!events.length) {
        tbody.innerHTML =
            `<tr><td colspan="6" class="empty">На выбранный горизонт событий нет</td></tr>`;
        return;
    }

    tbody.innerHTML = "";
    for (const e of events) {
        const tr = document.createElement("tr");
        tr.innerHTML = `
            <td>${formatDate(e.date)}</td>
            <td><strong>${e.inventory_no}</strong></td>
            <td>${e.type_name}</td>
            <td>${e.manufacturer_name}</td>
            <td>${e.model_name}</td>
            <td><span class="badge badge--${e.code}">${e.code}</span> ${e.name}</td>
        `;
        tbody.appendChild(tr);
    }
}


// ------------------------------------------------------------
// 9.1. КАЛЕНДАРЬ
// ------------------------------------------------------------

function renderCalendar() {
    const grid = el("calendar-grid");
    const title = el("calendar-title");
    if (!grid || !title) return;

    const year = calendarMonth.getFullYear();
    const month = calendarMonth.getMonth();

    title.textContent = `${MONTH_NAMES[month]} ${year}`;

    // Первый день месяца и сдвиг к понедельнику
    const firstDay = new Date(year, month, 1);
    const jsWeekday = firstDay.getDay();        // 0=Sun, 1=Mon, ..., 6=Sat
    const leadingEmpty = (jsWeekday + 6) % 7;   // сдвиг для «Пн=0»

    const daysInMonth = new Date(year, month + 1, 0).getDate();

    // Фильтруем события на отображаемый месяц и группируем по номеру дня
    const byDay = {};
    for (const e of scheduleCache) {
        const d = new Date(e.date);
        if (d.getFullYear() === year && d.getMonth() === month) {
            const day = d.getDate();
            (byDay[day] = byDay[day] || []).push(e);
        }
    }

    // Сортируем события внутри дня по уровню (ТО → ТР → КР)
    for (const day in byDay) {
        byDay[day].sort((a, b) => a.level - b.level);
    }

    grid.innerHTML = "";

    // Пустые ячейки до первого дня месяца
    for (let i = 0; i < leadingEmpty; i++) {
        const cell = document.createElement("div");
        cell.className = "calendar__day calendar__day--empty";
        grid.appendChild(cell);
    }

    const today = new Date();
    const isCurrentMonth =
        today.getFullYear() === year && today.getMonth() === month;

    for (let day = 1; day <= daysInMonth; day++) {
        const cell = document.createElement("div");
        cell.className = "calendar__day";
        if (isCurrentMonth && today.getDate() === day) {
            cell.classList.add("calendar__day--today");
        }

        const num = document.createElement("div");
        num.className = "calendar__day-num";
        num.textContent = day;
        cell.appendChild(num);

        const events = byDay[day] || [];
        for (const e of events) {
            const ev = document.createElement("div");
            ev.className = `calendar__event badge--${e.code}`;
            ev.textContent = `${e.code} · ${e.inventory_no}`;
            ev.title =
                `${e.code} — ${e.name}\n` +
                `Оборудование: ${e.inventory_no}\n` +
                `Тип: ${e.type_name}\n` +
                `Модель: ${e.model_name}\n` +
                `Дата: ${formatDate(e.date)}`;
            cell.appendChild(ev);
        }

        grid.appendChild(cell);
    }

    // Добиваем последнюю неделю пустыми ячейками
    const totalCells = leadingEmpty + daysInMonth;
    const remainder = totalCells % 7;
    if (remainder) {
        for (let i = 0; i < 7 - remainder; i++) {
            const cell = document.createElement("div");
            cell.className = "calendar__day calendar__day--empty";
            grid.appendChild(cell);
        }
    }
}


// ------------------------------------------------------------
// 9.2. ПЕРЕКЛЮЧЕНИЕ ПРЕДСТАВЛЕНИЙ И НАВИГАЦИЯ ПО КАЛЕНДАРЮ
// ------------------------------------------------------------

function setScheduleView(view) {
    currentScheduleView = view;

    document.querySelectorAll(".view-btn").forEach(btn => {
        btn.classList.toggle("is-active", btn.dataset.view === view);
    });

    el("schedule-view-table").hidden = view !== "table";
    el("schedule-view-calendar").hidden = view !== "calendar";

    if (view === "calendar") {
        // Подгружаем события с горизонтом, покрывающим текущий месяц
        loadSchedule();
    } else {
        renderScheduleTable(scheduleCache, el("schedule-tbody"));
        const info = el("schedule-info");
        if (info) info.textContent = `Найдено событий: ${scheduleCache.length}`;
    }
}

document.querySelectorAll(".view-btn").forEach(btn => {
    btn.addEventListener("click", () => setScheduleView(btn.dataset.view));
});

el("cal-prev").addEventListener("click", () => {
    calendarMonth = new Date(
        calendarMonth.getFullYear(),
        calendarMonth.getMonth() - 1,
        1
    );
    loadSchedule();
});

el("cal-next").addEventListener("click", () => {
    calendarMonth = new Date(
        calendarMonth.getFullYear(),
        calendarMonth.getMonth() + 1,
        1
    );
    loadSchedule();
});

el("cal-today").addEventListener("click", () => {
    calendarMonth = new Date();
    loadSchedule();
});

el("sched-horizon").addEventListener("change", loadSchedule);
el("sched-refresh").addEventListener("click", loadSchedule);
el("sched-codes").addEventListener("change", loadSchedule);


// ============================================================
// 10. ИНИЦИАЛИЗАЦИЯ — строго в конце, после всех обработчиков
// ============================================================

(async function init() {
    try {
        await Promise.all([
            loadStatuses(),
            loadTypes(),
            loadManufacturers(),
            loadModelsForFilter(),
        ]);
        await loadEquipmentList();
        await loadSchedule();
    } catch (err) {
        alert(`Не удалось загрузить данные: ${err.message}\n` +
            `Проверьте, что API доступно по адресу ${API_BASE}`);
    }
})();