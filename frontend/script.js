const BACKEND_URL = "https://clinical-trial-backend-27zz.onrender.com";
const API = BACKEND_URL + "/api";

const TRIAL_PK = 1;            // database id of the trial shown on the dashboard
const TAMPER_INCREASE = 40;    // how much "Tamper" adds to the glucose value
const ETHERSCAN_TX = "https://sepolia.etherscan.io/tx/";
const MAX_AUTO_REFRESHES = 15; // while waiting for blockchain confirmation
const AUTO_REFRESH_MS = 6000;

let participants = [];
let refreshing = false;
let autoRefreshes = 0;
let autoTimer = null;
let recordIdEdited = false;

const $ = (id) => document.getElementById(id);


/* ------------------------------ helpers ------------------------------ */

async function request(path, options = {}) {
    const init = { ...options };

    if (init.body) {
        init.headers = { "Content-Type": "application/json" };
    }

    const response = await fetch(API + path, init);

    let data = null;
    try {
        data = await response.json();
    } catch (error) {
        data = null;
    }

    if (!response.ok) {
        throw new Error(
            describeError(data) || "Request failed (" + response.status + ")"
        );
    }

    return data;
}

function describeError(data) {
    if (!data) return "";
    if (data.detail) return data.detail;

    return Object.entries(data)
        .map(([field, messages]) =>
            field + ": " + [].concat(messages).join(" ")
        )
        .join(" | ");
}

function showMessage(type, text, txHash) {
    const box = $("message");

    box.className = "message " + type;
    box.textContent = text;

    if (txHash) {
        box.appendChild(document.createTextNode(" "));

        const link = document.createElement("a");
        link.href = ETHERSCAN_TX + txHash;
        link.target = "_blank";
        link.rel = "noopener";
        link.textContent = "View transaction on Etherscan";
        box.appendChild(link);
    }

    box.hidden = false;
}

function originalKey(id) {
    return "clinical_original_glucose_" + id;
}

function getOriginal(id) {
    try {
        return localStorage.getItem(originalKey(id));
    } catch (error) {
        return null;
    }
}

function setOriginal(id, value) {
    try {
        localStorage.setItem(originalKey(id), String(value));
    } catch (error) { /* ignore */ }
}

function clearOriginal(id) {
    try {
        localStorage.removeItem(originalKey(id));
    } catch (error) { /* ignore */ }
}


/* ------------------------------ dashboard ---------------------------- */

async function loadDashboard() {
    const alertBox = $("integrity-alert");

    try {
        const data = await request("/digital-twin/" + TRIAL_PK + "/");

        $("trial-name").textContent = data.trial_name;
        $("trial-id").textContent = data.trial_id;
        $("trial-status").textContent = data.status;
        $("participants").textContent = data.participants;
        $("centers").textContent = data.research_centers;
        $("records").textContent = data.clinical_records;
        $("verified").textContent = data.verified_records;
        $("tampered").textContent = data.tampered_records;
        $("pending").textContent = data.pending_records || 0;

        if (data.tampered_records > 0) {
            alertBox.textContent =
                "WARNING: " + data.tampered_records +
                " tampered record(s) detected! Please investigate.";
            alertBox.style.backgroundColor = "#fee2e2";
            alertBox.style.color = "#b91c1c";
        } else if (data.pending_records > 0) {
            alertBox.textContent =
                data.pending_records +
                " record(s) are not on the blockchain yet " +
                "(waiting for confirmation).";
            alertBox.style.backgroundColor = "#fef3c7";
            alertBox.style.color = "#92400e";
        } else {
            alertBox.textContent =
                "All clinical records passed integrity verification.";
            alertBox.style.backgroundColor = "#dcfce7";
            alertBox.style.color = "#166534";
        }
    } catch (error) {
        alertBox.textContent =
            "Unable to connect to the backend. It may be waking up - " +
            "wait a few seconds and press Refresh.";
        alertBox.style.backgroundColor = "#fef3c7";
        alertBox.style.color = "#92400e";

        console.error("Dashboard error:", error);
    }
}


/* ------------------------------ add record --------------------------- */

async function loadParticipants() {
    const list = $("participant-list");

    try {
        const result = await request("/participants/");
        participants = result.results || result;

        list.replaceChildren();

        for (const participant of participants) {
            const option = document.createElement("option");
            option.value = participant.participant_id;
            list.appendChild(option);
        }

        if (!$("f-participant").value && participants.length > 0) {
            $("f-participant").value = participants[0].participant_id;
        }
    } catch (error) {
        console.error("Participants error:", error);
    }
}

async function ensureParticipant(participantId) {
    const wanted = participantId.trim().toLowerCase();

    const findIt = () => participants.find(
        (p) => p.participant_id.toLowerCase() === wanted
    );

    let participant = findIt();
    if (participant) return participant;

    // not in our list - reload it in case it was created elsewhere
    await loadParticipants();
    participant = findIt();
    if (participant) return participant;

    // genuinely new: attach it to the dashboard's trial and the first center
    const centersResult = await request("/centers/");
    const centers = centersResult.results || centersResult;

    if (centers.length === 0) {
        throw new Error("No research center exists yet, so a new participant cannot be created.");
    }

    participant = await request("/participants/", {
        method: "POST",
        body: JSON.stringify({
            participant_id: participantId.trim(),
            trial: TRIAL_PK,
            center: centers[0].id,
            status: "Active"
        })
    });

    participants.push(participant);

    const option = document.createElement("option");
    option.value = participant.participant_id;
    $("participant-list").appendChild(option);

    return participant;
}

function suggestRecordId(rows) {
    if (recordIdEdited) return;

    let highest = 0;

    for (const row of rows) {
        const match = /^REC(\d+)$/i.exec(row.record_id);
        if (match) highest = Math.max(highest, Number(match[1]));
    }

    $("f-record-id").value =
        "REC" + String(highest + 1).padStart(3, "0");
}

async function saveRecord(event) {
    event.preventDefault();

    const button = $("save-button");
    button.disabled = true;
    button.textContent = "Saving...";

    try {
        const participant = await ensureParticipant($("f-participant").value);

        const result = await request("/clinical-data/", {
            method: "POST",
            body: JSON.stringify({
                record_id: $("f-record-id").value.trim(),
                participant: participant.id,
                trial: participant.trial,
                blood_pressure: $("f-bp").value.trim(),
                blood_glucose: Number($("f-glucose").value),
                treatment: $("f-treatment").value,
                timestamp: new Date().toISOString()
            })
        });

        if (result.chain_error) {
            showMessage(
                "warning",
                "Record " + result.record_id + " was saved in the database, " +
                "but its hash is NOT on the blockchain: " + result.chain_error +
                " Use \"Store on blockchain\" in the table to retry."
            );
        } else {
            showMessage(
                "success",
                "Record " + result.record_id + " saved. Its hash was sent " +
                "to the Sepolia blockchain - the status turns VERIFIED " +
                "once the transaction is confirmed (about 10-30 seconds).",
                result.tx_hash
            );
        }

        $("f-glucose").value = "";
        recordIdEdited = false;

        autoRefreshes = 0;
        await refreshAll();
    } catch (error) {
        showMessage("danger", "Could not save the record: " + error.message);
    } finally {
        button.disabled = false;
        button.textContent = "Save & store on blockchain";
    }
}

/* ------------------------------ records table ------------------------ */

function makeCell(row, text) {
    const cell = document.createElement("td");
    cell.textContent = text;
    row.appendChild(cell);
    return cell;
}

function makeButton(label, className, onClick) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "btn small " + className;
    button.textContent = label;
    button.addEventListener("click", () => onClick(button));
    return button;
}

const STATUS_STYLE = {
    VERIFIED:     { label: "VERIFIED",          css: "verified" },
    TAMPERED:     { label: "TAMPERED",          css: "tampered" },
    NOT_ON_CHAIN: { label: "NOT ON BLOCKCHAIN", css: "pending" },
    ERROR:        { label: "CHECK FAILED",      css: "error" }
};

function buildRows(record) {
    const style = STATUS_STYLE[record.status] || STATUS_STYLE.ERROR;

    const row = document.createElement("tr");
    row.className = "row-" + style.css;

    makeCell(row, record.record_id);
    makeCell(row, record.participant);
    makeCell(row, record.blood_pressure);
    makeCell(row, Number(record.blood_glucose));
    makeCell(row, record.treatment);

    const statusCell = document.createElement("td");
    const badge = document.createElement("span");
    badge.className = "badge " + style.css;
    badge.textContent = style.label;
    statusCell.appendChild(badge);
    row.appendChild(statusCell);

    // hash details (hidden until "Hashes" is pressed)
    const detailsRow = document.createElement("tr");
    detailsRow.className = "details-row";
    detailsRow.hidden = true;

    const detailsCell = document.createElement("td");
    detailsCell.colSpan = 7;

    const dbLine = document.createElement("div");
    dbLine.append("Database hash (recomputed now):  ");
    const dbCode = document.createElement("code");
    dbCode.textContent = record.database_hash;
    dbLine.appendChild(dbCode);

    const chainLine = document.createElement("div");
    chainLine.append("Blockchain hash (stored on Sepolia):  ");
    const chainCode = document.createElement("code");
    chainCode.textContent = record.blockchain_hash || "(nothing stored yet)";
    chainLine.appendChild(chainCode);

    detailsCell.append(dbLine, chainLine);

    if (record.error) {
        const errorLine = document.createElement("div");
        errorLine.textContent = "Error: " + record.error;
        detailsCell.appendChild(errorLine);
    }

    detailsRow.appendChild(detailsCell);

    // actions
    const actionsCell = document.createElement("td");
    const actions = document.createElement("div");
    actions.className = "row-actions";

    actions.appendChild(
        makeButton("Hashes", "", () => {
            detailsRow.hidden = !detailsRow.hidden;
        })
    );

    if (record.status === "NOT_ON_CHAIN") {
        actions.appendChild(
            makeButton("Store on blockchain", "primary",
                (button) => anchorRecord(record, button))
        );
    } else {
        actions.appendChild(
            makeButton("Tamper", "danger",
                (button) => tamperRecord(record, button))
        );
    }

    const original = getOriginal(record.id);
    if (original !== null && Number(original) !== Number(record.blood_glucose)) {
        actions.appendChild(
            makeButton("Restore", "",
                (button) => restoreRecord(record, button))
        );
    }

    actionsCell.appendChild(actions);
    row.appendChild(actionsCell);

    return [row, detailsRow];
}

async function loadRecords() {
    const table = $("records-table");

    try {
        const rows = await request("/clinical-data/verify_all/");

        const fragment = document.createDocumentFragment();

        for (const record of rows) {
            fragment.append(...buildRows(record));
        }

        if (rows.length === 0) {
            const empty = document.createElement("tr");
            makeCell(empty, "No clinical records yet - add one above.")
                .colSpan = 7;
            fragment.appendChild(empty);
        }

        table.replaceChildren(fragment);
        suggestRecordId(rows);

        return rows;
    } catch (error) {
        const failed = document.createElement("tr");
        makeCell(failed, "Unable to load clinical records: " + error.message)
            .colSpan = 7;
        table.replaceChildren(failed);

        console.error("Records error:", error);
        return null;
    }
}

async function refreshAll() {
    if (refreshing) return;
    refreshing = true;

    clearTimeout(autoTimer);

    const refreshButton = $("refresh-button");
    refreshButton.disabled = true;

    try {
        const [, rows] = await Promise.all([loadDashboard(), loadRecords()]);

        // keep checking while hashes are still waiting to be confirmed
        const waiting = rows && rows.some((r) => r.status === "NOT_ON_CHAIN");

        if (waiting && autoRefreshes < MAX_AUTO_REFRESHES) {
            autoRefreshes += 1;
            autoTimer = setTimeout(refreshAll, AUTO_REFRESH_MS);
        }
    } finally {
        refreshing = false;
        refreshButton.disabled = false;
    }
}


/* ------------------------------ row actions -------------------------- */

async function tamperRecord(record, button) {
    button.disabled = true;

    try {
        if (getOriginal(record.id) === null) {
            setOriginal(record.id, record.blood_glucose);
        }

        const tamperedValue =
            Math.round((Number(record.blood_glucose) + TAMPER_INCREASE) * 10) / 10;

        await request("/clinical-data/" + record.id + "/", {
            method: "PATCH",
            body: JSON.stringify({ blood_glucose: tamperedValue })
        });

        showMessage(
            "danger",
            "Record " + record.record_id + " was edited directly in the " +
            "database (glucose " + Number(record.blood_glucose) + " -> " +
            tamperedValue + "). The blockchain still holds the original hash, " +
            "so the integrity check now fails."
        );

        autoRefreshes = MAX_AUTO_REFRESHES;
        await refreshAll();
    } catch (error) {
        showMessage("danger", "Could not tamper with the record: " + error.message);
        button.disabled = false;
    }
}

async function restoreRecord(record, button) {
    button.disabled = true;

    try {
        const original = Number(getOriginal(record.id));

        await request("/clinical-data/" + record.id + "/", {
            method: "PATCH",
            body: JSON.stringify({ blood_glucose: original })
        });

        clearOriginal(record.id);

        showMessage(
            "success",
            "Record " + record.record_id + " restored to its original value (" +
            original + "). The hashes match again."
        );

        autoRefreshes = MAX_AUTO_REFRESHES;
        await refreshAll();
    } catch (error) {
        showMessage("danger", "Could not restore the record: " + error.message);
        button.disabled = false;
    }
}

async function anchorRecord(record, button) {
    button.disabled = true;
    button.textContent = "Sending...";

    try {
        const result = await request(
            "/clinical-data/" + record.id + "/anchor/",
            { method: "POST" }
        );

        showMessage(
            "success",
            "Hash of " + record.record_id + " sent to the Sepolia blockchain. " +
            "It turns VERIFIED once the transaction is confirmed.",
            result.tx_hash
        );

        autoRefreshes = 0;
        await refreshAll();
    } catch (error) {
        showMessage("danger", "Could not store the hash: " + error.message);
        button.disabled = false;
        button.textContent = "Store on blockchain";
    }
}


/* ------------------------------ start up ----------------------------- */

$("record-form").addEventListener("submit", saveRecord);
$("refresh-button").addEventListener("click", () => {
    autoRefreshes = 0;
    refreshAll();
});
$("f-record-id").addEventListener("input", () => {
    recordIdEdited = true;
});

$("integrity-alert").textContent =
    "Connecting to the server (free hosting can take up to a minute " +
    "to wake up)...";

loadParticipants();
refreshAll();