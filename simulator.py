# simulator.py (New Stateful Version with Demo Mode)

import requests
import json
import random
import time
import schedule
from datetime import datetime, timedelta
import os

# --- CONFIGURATION ---
# The URL will be provided by an environment variable on Render
API_URL = os.environ.get("WEB_SERVICE_URL")
SIMULATION_INTERVAL_SECONDS = 10 # How often to send data for all villages
VILLAGES = [
    'mawlynnong_meghalaya', 'ziro_arunachal', 'majuli_assam',
    'khonoma_nagaland', 'moirang_manipur', 'pelling_sikkim',
    'champhai_mizoram', 'unakoti_tripura'
]

# --- STATE MANAGEMENT (THE "MEMORY") ---
village_states = {}
for village in VILLAGES:
    village_states[village] = {
        "status": "normal",
        "contaminated_until": None
    }

def update_village_states():
    """
    This function manages the state of the villages.
    - It can randomly trigger a new contamination event.
    - It resets villages to "normal" after a contamination event ends.
    """
    now = datetime.now()
    
    for village, state in village_states.items():
        if state["status"] == "contaminated" and now > state["contaminated_until"]:
            state["status"] = "normal"
            state["contaminated_until"] = None
            print(f"✅ Event Resolved: Water in {village} is back to normal.")

    if random.random() < 0.05:
        # Exclude majuli_assam from being randomly chosen
        normal_villages = [v for v, s in village_states.items() if s["status"] == "normal" and v != 'majuli_assam']
        if normal_villages:
            village_to_contaminate = random.choice(normal_villages)
            contamination_duration = timedelta(minutes=random.uniform(2, 5))
            village_states[village_to_contaminate]["status"] = "contaminated"
            village_states[village_to_contaminate]["contaminated_until"] = now + contamination_duration
            print(f"🚨 New Contamination Event: Water in {village_to_contaminate} is now contaminated for {contamination_duration.total_seconds() / 60:.1f} minutes!")

def generate_water_data(village, status):
    """Generates water quality data based on the village's current status."""
    
    # --- HACKATHON DEMO FEATURE ---
    # If the village is Majuli, ALWAYS report it as contaminated for the demo.
    if village == 'majuli_assam':
        return {
            "village": village,
            "ph": round(random.uniform(4.5, 6.0), 2),
            "turbidity": round(random.uniform(10.0, 25.0), 2),
            "contaminants": {"e-coli": "high", "arsenic": "critical"}
        }
    # --- END DEMO FEATURE ---

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
    update_village_states()

    for village, state in village_states.items():
        # For the demo, Majuli's status is forced inside generate_water_data
        current_status = 'contaminated' if village == 'majuli_assam' else state["status"]
        data = generate_water_data(village, current_status)
        
        try:
            # Check if API_URL is set before trying to post
            if API_URL:
                requests.post(API_URL, data=json.dumps(data), headers={'Content-Type': 'application/json'})
            else:
                print("  ⚠️ API_URL not set. Skipping send.")
                
            status_emoji = "🔴" if current_status == "contaminated" else "🟢"
            # Add a special emoji for the demo village
            if village == 'majuli_assam':
                status_emoji = "🔴 (DEMO)"
            
            print(f"  {status_emoji} Sent data for {village}: Turbidity={data['turbidity']:.2f}")
        
        except requests.exceptions.RequestException as e:
            print(f"  ❌ Connection Error for {village}: {e}")
            # Continue to the next village instead of stopping the whole batch
            continue 
    print("-------------------------------------------\n")


if __name__ == "__main__":
    print("Starting Stateful IoT Water Quality Simulator...")
    if not API_URL:
        print("WARNING: WEB_SERVICE_URL environment variable is not set. Simulator will run but not send data.")
    print(f"Sending data for all villages every {SIMULATION_INTERVAL_SECONDS} seconds.")
    print("Press CTRL+C to stop.")
    
    schedule.every(SIMULATION_INTERVAL_SECONDS).seconds.do(send_all_village_data)
    
    while True:
        schedule.run_pending()
        time.sleep(1)