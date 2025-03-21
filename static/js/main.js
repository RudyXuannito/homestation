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
        body: JSON.stringify({ "state": state })  // ����������� ���������� ������
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`������ HTTP: ${response.status}`);
        }
        return response.json();
    })
    .then(data => console.log("����� �������:", data))
    .catch(error => console.error("������ �������:", error));
}

