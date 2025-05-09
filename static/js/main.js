function showSection(sectionId) {
            document.querySelectorAll('.content-section').forEach(section => {
                section.style.display = 'none';
            });
            document.getElementById(sectionId).style.display = 'block';
            if (sectionId === "cameras") {
              renderCameras();
            }
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
      const humPercent = hum !== null ? Math.min(100, Math.max(0, hum)) : 0;
      const tempDisplay = temp !== null ? `${temp}°C` : 'Ошибка';
      const humDisplay = hum !== null ? `${hum}%` : 'Ошибка';

      block.classList.add("sensor-block-tandh");
      block.innerHTML = `
        <div class="sensor-header">
          <div class="sensor-name">${name}
            <button class="delete-button" onclick="deleteSensor('${name}')">&times;</button>
          </div>
        </div>
        <div class="dual-meters">
          <div class="meter">
            <div class="thermometer-fill" style="height: ${tempPercent}%;"></div>
          </div>
          <div class="meter">
            <div class="hygrometer-fill" style="height: ${humPercent}%;"></div>
          </div>
        </div>
        <div style="margin-top: 10px;">
          <i class="fa-solid fa-temperature-half"></i>${tempDisplay} &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<i class="fa-solid fa-droplet"></i>${humDisplay}
        </div>
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

function toggleLEDModal(state) {
  if (!window.currentControlCameraIP) {
    alert("Эта камера не поддерживает управление LED");
    return;
  }

  fetch("/control_led", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ "state": state, "ip": window.currentControlCameraIP })
  })
  .then(response => {
    if (!response.ok) {
      throw new Error(`Ошибка HTTP: ${response.status}`);
    }
    return response.json();
  })
  .then(data => console.log("Ответ сервера:", data))
  .catch(error => console.error("Ошибка запроса:", error));
}

function renderCameras() {
  fetch("/api/cameras")
    .then(res => res.json())
    .then(cameras => {
      const container = document.getElementById("camera-container");
      container.innerHTML = '';

      cameras.forEach(cam => {
        const block = document.createElement("div");
        block.style = "display: flex; flex-direction: column; align-items: center; margin: 10px;";

        const label = document.createElement("div");
        label.className = "camera-header";
        label.style = "position: relative; width: 300px; text-align: left; margin-bottom: 5px;";
        
        label.innerHTML = `
          <span style="display: inline-block; padding-right: 30px;">${cam.name}</span>
          <button class="delete-button" onclick="deleteCamera('${cam.name}')" title="Удалить камеру">&times;</button>
        `;
        label.style = "text-align: center; font-weight: bold; margin-bottom: 5px;";
        block.appendChild(label);

        const img = document.createElement("img");
        img.src = `/video_stream?url=${encodeURIComponent(cam.url)}`;
        img.alt = cam.name;
        img.className = "img-fluid";
        img.style = "max-width: 300px;";

        let loaded = false;

        const fallback = () => {
          if (!loaded) {
            img.src = "/static/img/camera-offline.jpg";
          }
        };

        img.onload = () => {
          loaded = true;
          img.onclick = () => {
            document.getElementById("modalCameraImage").src = img.src;
            document.getElementById("cameraModalLabel").textContent = cam.name;
            // если у тебя разные камеры — здесь можно менять IP-адрес управления:
            window.currentControlCameraIP = cam.url.includes("192.168.31.91") ? "192.168.31.91" : null;
            const modal = new bootstrap.Modal(document.getElementById("cameraModal"));
            modal.show();
          };
        };
        
        img.onerror = () => {
          fallback();
        };

        // если через 4 секунды камера не загрузилась, меняем на заглушку
        setTimeout(fallback, 4000);

        block.appendChild(img);
        container.appendChild(block);
      });
    })
    .catch(err => console.error("Ошибка загрузки камер:", err));
}

function deleteCamera(name) {
  if (!confirm(`Удалить камеру "${name}"?`)) return;

  fetch(`/delete_camera/${encodeURIComponent(name)}`, {
    method: "DELETE"
  })
  .then(res => {
    if (res.ok) {
      renderCameras(); // обновим список
    } else {
      console.error("Ошибка при удалении камеры");
    }
  })
  .catch(err => console.error("Ошибка запроса:", err));
}

document.addEventListener("DOMContentLoaded", () => {
  document.getElementById("add-camera-form").addEventListener("submit", function (e) {
    e.preventDefault();
    const name = document.getElementById("camera-name").value;
    const url = document.getElementById("camera-url").value;
  
    fetch("/addcamera", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, url })
    })
    .then(res => res.json())
    .then(data => {
      document.getElementById("add-camera-message").textContent = data.message;
      document.getElementById("add-camera-form").reset();
      renderCameras();
    })
    .catch(err => {
      document.getElementById("add-camera-message").style.color = "red";
      document.getElementById("add-camera-message").textContent = "Ошибка: " + err.message;
    });
  });
});

function updateSensors() {
    fetch('/api/sensors')
      .then(res => res.json())
      .then(renderSensors)
      .catch(err => console.error("Sensor update error", err));
  }

  updateSensors(); // Initial load
  setInterval(updateSensors, 10000); // Every 10 sec