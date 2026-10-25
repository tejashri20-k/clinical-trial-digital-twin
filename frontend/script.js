const API_URL = "https://clinical-trial-backend-27zz.onrender.com/api/digital-twin/1/";
const RECORDS_URL = "https://clinical-trial-backend-27zz.onrender.com/api/clinical-data/";

async function loadDashboard() {
    const alertBox = document.getElementById("integrity-alert");

    try {
        const response = await fetch(API_URL);

        if (!response.ok) {
            throw new Error("Could not fetch trial data");
        }

        const data = await response.json();

        document.getElementById("trial-name").textContent =
            data.trial_name;

        document.getElementById("trial-id").textContent =
            data.trial_id;

        document.getElementById("trial-status").textContent =
            data.status;

        document.getElementById("participants").textContent =
            data.participants;

        document.getElementById("centers").textContent =
            data.research_centers;

        document.getElementById("records").textContent =
            data.clinical_records;

        document.getElementById("verified").textContent =
            data.verified_records;

        document.getElementById("tampered").textContent =
            data.tampered_records;

        if (data.tampered_records > 0) {
            alertBox.textContent =
                "WARNING: Tampered records detected! Please investigate.";
            alertBox.style.backgroundColor = "#fee2e2";
            alertBox.style.color = "#b91c1c";
        } else {
            alertBox.textContent =
                "All clinical records passed integrity verification.";
            alertBox.style.backgroundColor = "#dcfce7";
            alertBox.style.color = "#166534";
        }

    } catch (error) {
        alertBox.textContent =
            "Unable to connect to Django. Check that the backend is running.";
        alertBox.style.backgroundColor = "#fef3c7";
        alertBox.style.color = "#92400e";

        console.error("Dashboard error:", error);
    }
}

loadDashboard();

setInterval(loadDashboard, 5000);

async function loadRecords() {
    const table = document.getElementById("records-table");

    try {
        const response = await fetch(RECORDS_URL);

        if (!response.ok) {
            throw new Error("Could not fetch clinical records");
        }

        const result = await response.json();
        const records = result.results || result;

        table.innerHTML = "";

        for (const record of records) {
            const row = document.createElement("tr");

            const idCell = document.createElement("td");
            idCell.textContent = record.record_id;

            const statusCell = document.createElement("td");
            statusCell.textContent = "Checking...";

            try {
            const verifyResponse = await fetch(
                RECORDS_URL + record.id + "/verify_integrity/"
            );

            if (!verifyResponse.ok) {
                throw new Error("Verification failed");
            }

            const verification = await verifyResponse.json();

            statusCell.textContent = verification.status;

            if (verification.status.toLowerCase() === "verified") {
                statusCell.style.color = "#15803d";
            } else {
                statusCell.style.color = "#b91c1c";
            }
        } catch (error) {
            statusCell.textContent = "Verification Error";
            statusCell.style.color = "#92400e";
        }

            row.appendChild(idCell);
            row.appendChild(statusCell);
            table.appendChild(row);
        }
    } catch (error) {
        table.innerHTML =
            '<tr><td colspan="2">Unable to load clinical records.</td></tr>';

        console.error("Records error:", error);
    }
}

loadRecords();
//setInterval(loadRecords, 5000);