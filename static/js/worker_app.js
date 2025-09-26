// static/js/worker_app.js

// Register the Service Worker for PWA capabilities
if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/serviceworker.js')
        .then(reg => console.log('Service worker registered successfully'))
        .catch(err => console.log('Service worker registration failed: ', err));
}

document.addEventListener('DOMContentLoaded', () => {
    const reportForm = document.getElementById('report-form');
    const syncStatus = document.getElementById('sync-status');
    const dbName = 'aquaalertDB';
    let db;

    // 1. Open the IndexedDB database
    const request = indexedDB.open(dbName, 1);

    request.onerror = (event) => {
        console.error("Database error: " + event.target.errorCode);
    };

    request.onupgradeneeded = (event) => {
        db = event.target.result;
        const objectStore = db.createObjectStore("offlineReports", { keyPath: "id", autoIncrement:true });
        console.log("Object store created.");
    };

    request.onsuccess = (event) => {
        db = event.target.result;
        console.log("Database opened successfully.");
        // Try to sync any saved reports when the app loads
        syncOfflineReports(); 
    };

    // 2. Intercept form submission
    reportForm.addEventListener('submit', (e) => {
        e.preventDefault();

        const village = document.getElementById('village').value;
        const ageGroup = document.getElementById('age-group').value;
        const symptoms = Array.from(document.querySelectorAll('input[name="symptom"]:checked')).map(cb => cb.value);

        if (!village || symptoms.length === 0) {
            alert('Please select a village and at least one symptom.');
            return;
        }

        const report = { village, ageGroup, symptoms, timestamp: new Date().toISOString() };

        // Check if online
        if (navigator.onLine) {
            sendReportToServer(report);
        } else {
            saveReportLocally(report);
        }
        reportForm.reset();
    });

    // 3. Function to send data to the server
    function sendReportToServer(report) {
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
        fetch('/api/submit-report/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken,
            },
            body: JSON.stringify(report)
        })
        .then(response => response.json())
        .then(data => {
            if(data.status === 'success') {
                updateSyncStatus('Report submitted successfully online!', 'success');
            } else {
                // If server fails, save it locally for later
                saveReportLocally(report);
            }
        })
        .catch(error => {
            console.error('Fetch Error:', error);
            saveReportLocally(report);
        });
    }

    // 4. Function to save data to IndexedDB
    function saveReportLocally(report) {
        const transaction = db.transaction(["offlineReports"], "readwrite");
        const objectStore = transaction.objectStore("offlineReports");
        const request = objectStore.add(report);

        request.onsuccess = () => {
            updateSyncStatus('You are offline. Report saved and will sync later.', 'offline');
        };
        request.onerror = (event) => {
            console.error('Error saving report locally:', event.target.error);
            updateSyncStatus('Could not save report offline. Please try again.', 'error');
        };
    }

    // 5. Function to sync all offline data
    function syncOfflineReports() {
        if (!navigator.onLine) return;

        const transaction = db.transaction(["offlineReports"], "readwrite");
        const objectStore = transaction.objectStore("offlineReports");
        const getAllRequest = objectStore.getAll();

        getAllRequest.onsuccess = () => {
            const reports = getAllRequest.result;
            if (reports.length > 0) {
                updateSyncStatus(`Syncing ${reports.length} offline report(s)...`, 'syncing');
                reports.forEach(report => {
                    sendReportToServer(report);
                    // On successful send, we should remove it from IndexedDB
                    // A more robust implementation would wait for server confirmation before deleting.
                    objectStore.delete(report.id);
                });
                updateSyncStatus('All offline reports have been synced!', 'success');
            } else {
                updateSyncStatus('App is up to date.', 'success');
            }
        };
    }

    function updateSyncStatus(message, type) {
        syncStatus.textContent = message;
        syncStatus.className = `status-${type}`; // for styling
    }

    // Listen for online/offline events
    window.addEventListener('online', syncOfflineReports);
    window.addEventListener('offline', () => updateSyncStatus('You are now offline.', 'offline'));
});