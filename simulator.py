# simulator.py (New Stateful Version)

import requests
import json
import random
import time
import schedule
from datetime import datetime, timedelta

# --- CONFIGURATION ---
# --- CONFIGURATION ---
import os
# The URL will be provided by an environment variable on Render
API_URL = os.environ.get("WEB_SERVICE_URL")
SIMULATION_INTERVAL_SECONDS = 10 # How often to send data for all villages
VILLAGES = [
    'mawlynnong_meghalaya', 'ziro_arunachal', 'majuli_assam',
    'khonoma_nagaland', 'moirang_manipur', 'pelling_sikkim',
    'champhai_mizoram', 'unakoti_tripura'
]

# --- STATE MANAGEMENT (THE "MEMORY") ---
# This dictionary will hold the current status of each village
village_states = {}
for village in VILLAGES:
    village_states[village] = {
        "status": "normal", # Can be "normal" or "contaminated"
        "contaminated_until": None # Timestamp for when contamination ends
    }

def update_village_states():
    """
    This function manages the state of the villages.
    - It can randomly trigger a new contamination event.
    - It resets villages to "normal" after a contamination event ends.
    """
    now = datetime.now()
    
    # Check for villages that should return to normal
    for village, state in village_states.items():
        if state["status"] == "contaminated" and now > state["contaminated_until"]:
            state["status"] = "normal"
            state["contaminated_until"] = None
            print(f"✅ Event Resolved: Water in {village} is back to normal.")

    # Small chance to start a NEW contamination event in a random normal village
    if random.random() < 0.05: # 5% chance every interval to start an event
        normal_villages = [v for v, s in village_states.items() if s["status"] == "normal"]
        if normal_villages:
            village_to_contaminate = random.choice(normal_villages)
            contamination_duration = timedelta(minutes=random.uniform(2, 5)) # Event lasts 2-5 mins
            village_states[village_to_contaminate]["status"] = "contaminated"
            village_states[village_to_contaminate]["contaminated_until"] = now + contamination_duration
            print(f"🚨 New Contamination Event: Water in {village_to_contaminate} is now contaminated for {contamination_duration.total_seconds() / 60:.1f} minutes!")

def generate_water_data(village, status):
    """Generates water quality data based on the village's current status."""
    if status == "contaminated":
        ph = round(random.uniform(4.5, 6.0), 2)
        turbidity = round(random.uniform(8.0, 20.0), 2)
        contaminants = {"e-coli": "high", "arsenic": "moderate"}
    else: # status == "normal"
        ph = round(random.uniform(6.8, 7.8), 2)
        turbidity = round(random.uniform(0.5, 4.5), 2)
        contaminants = {"e-coli": "low", "arsenic": "safe"}

    return { "village": village, "ph": ph, "turbidity": turbidity, "contaminants": contaminants }

def send_all_village_data():
    """
    Updates states, then generates and sends data for ALL villages.
    """
    print("--- Sending new batch of sensor data ---")
    update_village_states() # Decide if any new events start or end

    for village, state in village_states.items():
        data = generate_water_data(village, state["status"])
        
        try:
            requests.post(API_URL, data=json.dumps(data), headers={'Content-Type': 'application/json'})
            status_emoji = "🔴" if state["status"] == "contaminated" else "🟢"
            print(f"  {status_emoji} Sent data for {village}: Turbidity={data['turbidity']:.2f}")
        
        except requests.exceptions.ConnectionError:
            print(f"  ❌ Connection Error: Could not connect to the Django server.")
            # Stop the batch if the server is down
            break 
    print("-------------------------------------------\n")


if __name__ == "__main__":
    print("Starting Stateful IoT Water Quality Simulator...")
    print(f"Sending data for all villages every {SIMULATION_INTERVAL_SECONDS} seconds.")
    print("Press CTRL+C to stop.")
    
    schedule.every(SIMULATION_INTERVAL_SECONDS).seconds.do(send_all_village_data)
    
    while True:
        schedule.run_pending()
        time.sleep(1)