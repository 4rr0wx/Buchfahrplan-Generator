const routeSelect = document.querySelector("#route-select");
const startTimeInput = document.querySelector("#start-time");
const dwellInput = document.querySelector("#dwell");
const generateBtn = document.querySelector("#generate-btn");
const saveBtn = document.querySelector("#save-btn");
const downloadBtn = document.querySelector("#download-btn");
const tableBody = document.querySelector("#timetable-table tbody");
const rowTemplate = document.querySelector("#row-template");

let currentTimetable = null;

document.addEventListener("DOMContentLoaded", async () => {
  startTimeInput.value = defaultStartTime();
  await loadRoutes();
});

generateBtn.addEventListener("click", async () => {
  const routeId = routeSelect.value;
  if (!routeId) {
    alert("Bitte eine Strecke auswählen.");
    return;
  }

  const startTime = startTimeInput.value;
  if (!startTime) {
    alert("Bitte eine Startzeit festlegen.");
    return;
  }

  try {
    const response = await fetch("/api/timetables", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        route_id: routeId,
        start_time: toFullIso(startTime),
        dwell_minutes: Number.parseInt(dwellInput.value || "2", 10),
      }),
    });
    if (!response.ok) {
      throw new Error("Fehler beim Erstellen des Fahrplans.");
    }
    currentTimetable = await response.json();
    renderTable(currentTimetable.entries);
    toggleActions(true);
  } catch (error) {
    console.error(error);
    alert("Grundfahrplan konnte nicht generiert werden.");
  }
});

saveBtn.addEventListener("click", async () => {
  if (!currentTimetable) return;
  const payload = {
    entries: collectEntries(),
  };

  try {
    const response = await fetch(`/api/timetables/${currentTimetable.id}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!response.ok) throw new Error();
    currentTimetable = await response.json();
    alert("Fahrplan gespeichert.");
  } catch {
    alert("Speichern fehlgeschlagen.");
  }
});

downloadBtn.addEventListener("click", () => {
  if (!currentTimetable) return;
  window.open(`/api/timetables/${currentTimetable.id}/pdf`, "_blank");
});

async function loadRoutes() {
  try {
    const response = await fetch("/api/routes");
    const data = await response.json();
    routeSelect.innerHTML = "";
    data.routes.forEach((route) => {
      const option = document.createElement("option");
      option.value = route.id;
      option.textContent = `${route.name} (${route.country})`;
      routeSelect.append(option);
    });
    if (data.routes[0]) {
      routeSelect.value = data.routes[0].id;
    }
  } catch (error) {
    console.error(error);
  }
}

function renderTable(entries) {
  tableBody.innerHTML = "";
  entries.forEach((entry) => {
    const fragment = rowTemplate.content.cloneNode(true);
    const row = fragment.querySelector("tr");
    row.dataset.stationId = entry.station_id;
    row.dataset.stationName = entry.station_name;
    row.dataset.arrivalIso = entry.arrival || "";
    row.dataset.departureIso = entry.departure || "";

    fragment.querySelector(".station").textContent = entry.station_name;

    const arrivalInput = fragment.querySelector(".arrival");
    const departureInput = fragment.querySelector(".departure");
    const trackInput = fragment.querySelector(".track");
    const remarksInput = fragment.querySelector(".remarks");

    arrivalInput.value = entry.arrival ? toTime(entry.arrival) : "";
    departureInput.value = entry.departure ? toTime(entry.departure) : "";
    trackInput.value = entry.track || "";
    remarksInput.value = entry.remarks || "";

    tableBody.append(fragment);
  });
}

function collectEntries() {
  const rows = Array.from(tableBody.querySelectorAll("tr"));
  return rows.map((row) => {
    const arrivalInput = row.querySelector(".arrival");
    const departureInput = row.querySelector(".departure");
    const trackInput = row.querySelector(".track");
    const remarksInput = row.querySelector(".remarks");
    return {
      station_id: row.dataset.stationId,
      station_name: row.dataset.stationName,
      arrival: normalizeTime(arrivalInput.value, row.dataset.arrivalIso),
      departure: normalizeTime(departureInput.value, row.dataset.departureIso),
      track: trackInput.value || null,
      remarks: remarksInput.value || null,
    };
  });
}

function normalizeTime(timeValue, fallbackIso) {
  if (!timeValue) return null;
  const base = fallbackIso ? new Date(fallbackIso) : new Date();
  const [hours, minutes] = timeValue.split(":").map((val) => Number.parseInt(val, 10));
  base.setHours(hours);
  base.setMinutes(minutes);
  base.setSeconds(0);
  base.setMilliseconds(0);
  return base.toISOString();
}

function toTime(isoString) {
  const date = new Date(isoString);
  return `${pad(date.getHours())}:${pad(date.getMinutes())}`;
}

function defaultStartTime() {
  const now = new Date();
  now.setMinutes(Math.ceil(now.getMinutes() / 5) * 5);
  now.setSeconds(0);
  now.setMilliseconds(0);
  return now.toISOString().slice(0, 16);
}

function toFullIso(localValue) {
  const base = new Date(localValue);
  return base.toISOString();
}

function pad(value) {
  return value.toString().padStart(2, "0");
}

function toggleActions(enabled) {
  saveBtn.disabled = !enabled;
  downloadBtn.disabled = !enabled;
}

toggleActions(false);
