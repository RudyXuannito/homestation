function showSection(sectionId) {
            document.querySelectorAll('.content-section').forEach(section => {
                section.style.display = 'none';
            });
            document.getElementById(sectionId).style.display = 'block';
        }
function toggleLED(state) {
    fetch("/control_led", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ "state": state })  
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`Error HTTP: ${response.status}`);
        }
        return response.json();
    })
    .then(data => console.log("Answer server:", data))
    .catch(error => console.error("Error zaprosa:", error));
}
function renderSensors(data) {
  const container = document.getElementById("sensor-container");
  container.innerHTML = ''; // Clear previous content

  data.forEach(sensor => {
    const name = sensor.name;
    const type = sensor.type;
    const block = document.createElement("div");
    block.className = "sensor-block";

    if (type === "tandh") {
      const temp = sensor.temperature;
      const hum = sensor.humidity;
      const tempPercent = temp !== null ? Math.min(100, Math.max(0, temp)) : 0;
      const humidityDisplay = hum !== null ? `${hum}%` : 'Ошибка';

      block.innerHTML = `
        <div class="sensor-header">
        <div class="sensor-name">${name}<button class="delete-button" onclick="deleteSensor('${name}')">&times;</button></div>
        </div>
        <div class="thermometer">
          <div class="thermometer-fill" style="height: ${tempPercent}%;"></div>
        </div>
        <div><i class="fa-solid fa-temperature-half"></i> ${temp !== null ? `${temp}°C` : 'Ошибка'}</div>
        <div class="humidity"><i class="fa-solid fa-droplet"></i> ${humidityDisplay}</div>
      `;
    }

    if (type === "w") {
      const level = sensor.water;
      let statusDisplay = "Неизвестно";
      let statusClass = "water-unknown";
    
      if (level !== null) {
        if (level <= 50) {
          statusDisplay = "Сухо";
          statusClass = "water-ok";
        } else if (level <= 200) {
          statusDisplay = "Вода обнаружена!";
          statusClass = "water-detected";
        } else {
          statusDisplay = "Опасность! Уровень воды высокий!";
          statusClass = "water-danger";
        }
      }
    
      block.innerHTML = `
        <div class="sensor-header">
          <div class="sensor-name">${name}<button class="delete-button" onclick="deleteSensor('${name}')">&times;</button></div>
        </div>
        <div class="water-status ${statusClass}">
          <div class="droplet-icon">
            <i class="fa-solid fa-droplet"></i>
          </div>
          <div class="status-text">${statusDisplay}</div>
        </div>
      `;
        }

    container.appendChild(block);
  });
}

document.addEventListener("DOMContentLoaded", function () {
  const form = document.getElementById("add-sensor-form");
  const nameInput = document.getElementById("sensor-name");
  const urlInput = document.getElementById("sensor-url");
  const typeInput = document.getElementById("sensor-type");
  const messageBlock = document.getElementById("add-sensor-message");

  if (!form || !nameInput || !urlInput || !typeInput || !messageBlock) {
    console.error("Один из элементов формы не найден.");
    return;
  }

  form.addEventListener("submit", function (e) {
    e.preventDefault();

    const name = nameInput.value.trim();
    const url = urlInput.value.trim();
    const type = typeInput.value;

    fetch("/addsensor", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ name: name, url: url, type_: type })
    })
      .then(response => {
        if (!response.ok) throw new Error("Ошибка добавления датчика");
        return response.json();
      })
      .then(data => {
        messageBlock.textContent = "Сенсор добавлен!";
        messageBlock.style.color = "green";
        form.reset();
        updateSensors();
      })
      .catch(err => {
        messageBlock.textContent = "Ошибка: " + err.message;
        messageBlock.style.color = "red";
      });
  });
});


function deleteSensor(name) {
  if (!confirm(`Удалить сенсор "${name}"?`)) return;

  fetch(`/delete_sensor/${encodeURIComponent(name)}`, {
    method: "DELETE"
  })
  .then(res => {
    if (res.ok) {
      updateSensors(); // обновим список
    } else {
      console.error("Ошибка при удалении");
    }
  })
  .catch(err => console.error("Ошибка запроса удаления:", err));
}

function updateSensors() {
    fetch('/api/sensors')
      .then(res => res.json())
      .then(renderSensors)
      .catch(err => console.error("Sensor update error", err));
  }

  updateSensors(); // Initial load
  setInterval(updateSensors, 10000); // Every 10 sec