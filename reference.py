from flask import Flask, request, jsonify
from datetime import datetime
import random
import time
from collections import Counter
from flask_cors import CORS
import logging
import json
import os

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})  # Enable CORS for all API routes

# File paths for JSON storage
COMMANDS_FILE = "commands.json"
DEVICES_FILE = "devices.json"

# In-memory storage for devices and command history
DEVICES = {}
COMMAND_HISTORY = []

def load_commands():
    """Load command history from JSON file"""
    try:
        if os.path.exists(COMMANDS_FILE):
            with open(COMMANDS_FILE, 'r') as f:
                return json.load(f)
        return []
    except Exception as e:
        logger.error(f"Error loading commands: {str(e)}")
        return []

def save_commands(commands):
    """Save command history to JSON file"""
    try:
        with open(COMMANDS_FILE, 'w') as f:
            json.dump(commands, f, indent=2)
    except Exception as e:
        logger.error(f"Error saving commands: {str(e)}")

def load_devices():
    """Load devices from JSON file"""
    try:
        if os.path.exists(DEVICES_FILE):
            with open(DEVICES_FILE, 'r') as f:
                return json.load(f)
        return {}
    except Exception as e:
        logger.error(f"Error loading devices: {str(e)}")
        return {}

def save_devices(devices):
    """Save devices to JSON file"""
    try:
        with open(DEVICES_FILE, 'w') as f:
            json.dump(devices, f, indent=2)
    except Exception as e:
        logger.error(f"Error saving devices: {str(e)}")

def generate_device_id():
    return f"DEV_{int(time.time())}_{random.randint(1000, 9999)}"

@app.route('/api/devices', methods=['GET'])
def get_devices():
    """Get all registered devices"""
    try:
        logger.debug("GET /api/devices called")
        global DEVICES
        
        # Load devices from file
        DEVICES = load_devices()
        logger.debug(f"Loaded {len(DEVICES)} devices from file")

        devices_list = list(DEVICES.values())
        logger.debug(f"Returning {len(devices_list)} devices: {devices_list}")
        return jsonify(devices_list), 200
    except Exception as e:
        logger.error(f"Error in get_devices: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/devices', methods=['POST'])
def add_device():
    """Add a new device"""
    try:
        data = request.get_json()
        logger.debug(f"POST /api/devices called with data: {data}")
        
        if not data or 'name' not in data or 'type' not in data:
            return jsonify({"error": "Missing required fields"}), 400

        device_id = generate_device_id()
        device = {
            "id": device_id,
            "name": data['name'],
            "type": data['type'],
            "room": data.get('room', 'Unknown'),
            "isOn": False,
            "speed": 1 if data['type'] == 'fan' else None,
            "color": data.get('color', '#FFB800'),
            "lastUpdated": datetime.utcnow().isoformat()
        }
        
        # Load current devices
        DEVICES = load_devices()
        DEVICES[device_id] = device
        save_devices(DEVICES)
        
        logger.debug(f"Added new device: {device}")
        return jsonify(device), 201
    except Exception as e:
        logger.error(f"Error in add_device: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/devices/<device_id>', methods=['DELETE'])
def remove_device(device_id):
    """Remove a device"""
    DEVICES = load_devices()
    if device_id not in DEVICES:
        return jsonify({"error": "Device not found"}), 404
    
    del DEVICES[device_id]
    save_devices(DEVICES)
    return jsonify({"message": "Device removed successfully"}), 200

@app.route('/api/devices/<device_id>/state', methods=['PUT'])
def update_device_state(device_id):
    """Update device state (on/off, speed)"""
    DEVICES = load_devices()
    if device_id not in DEVICES:
        return jsonify({"error": "Device not found"}), 404

    data = request.get_json()
    device = DEVICES[device_id]
    
    if 'isOn' in data:
        device['isOn'] = data['isOn']
    
    if device['type'] == 'fan' and 'speed' in data:
        device['speed'] = max(1, min(3, data['speed']))
    
    if 'color' in data:
        device['color'] = data['color']
    
    device['lastUpdated'] = datetime.utcnow().isoformat()
    DEVICES[device_id] = device
    save_devices(DEVICES)
    
    return jsonify(device), 200

@app.route('/api/ping', methods=['GET'])
def ping():
    """Simply confirm the server is running."""
    return jsonify({ "alive": True }), 200

@app.route('/api/command', methods=['POST'])
def command():
    """
    Expects JSON payload:
      { "cmd": "<voice command text>" }
    Process command and store in commands.json
    """
    start_time = time.time() # Record start time
    data = request.get_json() or {}
    cmd = data.get('cmd', '').strip()

    if not cmd:
        return jsonify({ "status": "error", "result": "No command provided." }), 400

    # Simulate processing (e.g. classify voice, toggle a device, etc.)
    simulated_latency = random.uniform(50, 500) # Simulate processing time
    time.sleep(simulated_latency / 1000) # Simulate blocking I/O
    end_time = time.time() # Record end time
    response_time_ms = round((end_time - start_time) * 1000)

    result_text = f"Executed command: {cmd}"
    status = "success"

    # Simulate occasional errors
    if random.random() < 0.1: # 10% chance of failure
        status = "failed"
        result_text = f"Failed to execute command: {cmd}"

    # Create command entry
    command_entry = {
        "cmd": cmd,
        "status": status,
        "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "responseTime": response_time_ms,
        "user": "default_user",
        "response": result_text,
        "result": result_text
    }

    # Load existing commands
    global COMMAND_HISTORY
    COMMAND_HISTORY = load_commands()
    
    # Add new command
    COMMAND_HISTORY.append(command_entry)
    
    # Save to file
    save_commands(COMMAND_HISTORY)

    return jsonify({ "status": status, "result": result_text }), 200

START_TIME = time.time()

@app.route('/api/status', methods=['GET'])
def status():
    """
    Return device status: uptime, signal, battery, temperature, humidity, noise, accuracy.
    """
    uptime = int(time.time() - START_TIME)
    signal = random.randint(-70, -50)      # dBm
    battery = random.randint(70, 100)      # percent
    temperature = round(random.uniform(22, 28), 1)
    humidity = random.randint(40, 60)
    noise = random.randint(30, 50)
    accuracy = random.randint(85, 99)

    return jsonify({
        "uptime": uptime,
        "signal": signal,
        "battery": battery,
        "temperature": temperature,
        "humidity": humidity,
        "noise": noise,
        "accuracy": accuracy
    }), 200

@app.route('/api/analytics', methods=['GET'])
def analytics():
    """
    Return analytics data including total commands, successes, avg latency,
    last five commands, and command frequencies.
    """
    # Load commands from file
    global COMMAND_HISTORY
    COMMAND_HISTORY = load_commands()
    
    total = len(COMMAND_HISTORY)
    successes = sum(1 for entry in COMMAND_HISTORY if entry["status"] == "success")

    # Calculate average latency from history
    successful_commands_with_latency = [entry for entry in COMMAND_HISTORY if entry["status"] == "success" and "responseTime" in entry]
    avg_latency_ms = round(sum(entry["responseTime"] for entry in successful_commands_with_latency) / len(successful_commands_with_latency)) if successful_commands_with_latency else 0

    # Calculate command frequencies
    command_counts = Counter(entry["cmd"] for entry in COMMAND_HISTORY)
    command_frequency = [{"command": cmd, "count": count} for cmd, count in command_counts.items()]

    # Get last five entries
    last_five = COMMAND_HISTORY[-5:]

    # Extract historical latency data
    historical_latency = []
    for entry in COMMAND_HISTORY:
        if "responseTime" in entry and "timestamp" in entry:
            historical_latency.append({"timestamp": entry["timestamp"], "latency": entry["responseTime"]})

    return jsonify({
        "totalCommands": total,
        "successfulCommands": successes,
        "averageLatencyMs": avg_latency_ms,
        "lastFiveCommands": last_five,
        "commandFrequency": command_frequency,
        "historicalLatency": historical_latency
    }), 200

if __name__ == '__main__':
    logger.info("Starting server...")
    
    # Load existing devices
    DEVICES = load_devices()
    logger.info(f"Loaded {len(DEVICES)} devices from file")
    
    # Load existing commands
    COMMAND_HISTORY = load_commands()
    logger.info(f"Loaded {len(COMMAND_HISTORY)} existing commands")
    
    app.run(host='0.0.0.0', port=5000, debug=True) 