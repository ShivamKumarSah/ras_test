from flask import Flask, request, jsonify
from datetime import datetime
import random
import time
from collections import Counter
from flask_cors import CORS
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})  # Enable CORS for all API routes

# In-memory storage for devices and command history
DEVICES = {}
COMMAND_HISTORY = []

def generate_device_id():
    return f"DEV_{int(time.time())}_{random.randint(1000, 9999)}"

def create_sample_devices():
    """Create and return sample devices"""
    logger.debug("Creating sample devices")
    sample_devices = [
        {
            "id": generate_device_id(),
            "name": "Living Room Light",
            "type": "bulb",
            "room": "Living Room",
            "isOn": True,
            "color": "#FFB800",
            "lastUpdated": datetime.utcnow().isoformat()
        },
        {
            "id": generate_device_id(),
            "name": "Bedroom Fan",
            "type": "fan",
            "room": "Bedroom",
            "isOn": True,
            "speed": 3,
            "color": "#4ECDC4",
            "lastUpdated": datetime.utcnow().isoformat()
        },
        {
            "id": generate_device_id(),
            "name": "Bedroom Fan",
            "type": "fan",
            "room": "Living Room",
            "isOn": False,
            "speed": 1,
            "color": "#4ECDC4",
            "lastUpdated": datetime.utcnow().isoformat()
        }
    ]
    return sample_devices

@app.route('/api/devices', methods=['GET'])
def get_devices():
    """Get all registered devices"""
    try:
        logger.debug("GET /api/devices called")
        global DEVICES
        
        # If no devices exist, add sample devices
        if not DEVICES:
            logger.debug("No devices found, adding sample devices")
            sample_devices = create_sample_devices()
            for device in sample_devices:
                DEVICES[device["id"]] = device
            logger.debug(f"Added {len(sample_devices)} sample devices")
            logger.debug(f"Current devices: {DEVICES}")

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
        
        DEVICES[device_id] = device
        logger.debug(f"Added new device: {device}")
        return jsonify(device), 201
    except Exception as e:
        logger.error(f"Error in add_device: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/devices/<device_id>', methods=['DELETE'])
def remove_device(device_id):
    """Remove a device"""
    if device_id not in DEVICES:
        return jsonify({"error": "Device not found"}), 404
    
    del DEVICES[device_id]
    return jsonify({"message": "Device removed successfully"}), 200

@app.route('/api/devices/<device_id>/state', methods=['PUT'])
def update_device_state(device_id):
    """Update device state (on/off, speed)"""
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
    Simulate processing and return a result.
    """
    start_time = time.time() # Record start time
    data = request.get_json() or {}
    cmd = data.get('cmd', '').strip()

    if not cmd:
        return jsonify({ "status": "error", "result": "No command provided." }), 400

    # Simulate processing (e.g. classify voice, toggle a device, etc.)
    # In a real system, this is where you'd integrate with your hardware/service
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

    # Record into history using a proper timestamp and include response time
    COMMAND_HISTORY.append({
        "cmd": cmd,
        "status": status,
        "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "responseTime": response_time_ms, # Add responseTime
        "user": "default_user", # Add a placeholder user
        "response": result_text, # Add response text
        "result": result_text # Keep result for compatibility
    })

    return jsonify({ "status": status, "result": result_text }), 200

START_TIME = time.time()

@app.route('/api/status', methods=['GET'])
def status():
    """
    Return device status: uptime, signal, battery, temperature, humidity, noise, accuracy.
    """
    uptime = int(time.time() - START_TIME)
    # Simulate signal, battery, etc. with random or static values for now
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
    total = len(COMMAND_HISTORY)
    successes = sum(1 for entry in COMMAND_HISTORY if entry["status"] == "success")

    # Calculate average latency from history (only for successful commands with responseTime)
    successful_commands_with_latency = [entry for entry in COMMAND_HISTORY if entry["status"] == "success" and "responseTime" in entry]
    avg_latency_ms = round(sum(entry["responseTime"] for entry in successful_commands_with_latency) / len(successful_commands_with_latency)) if successful_commands_with_latency else 0

    # Calculate command frequencies
    command_counts = Counter(entry["cmd"] for entry in COMMAND_HISTORY)
    # Convert Counter object to a list of dicts for JSON
    command_frequency = [{"command": cmd, "count": count} for cmd, count in command_counts.items()]

    # Send back the last five entries (or fewer if <5)
    last_five = COMMAND_HISTORY[-5:]

    # Extract historical latency data for the graph
    historical_latency = []
    for entry in COMMAND_HISTORY:
        if "responseTime" in entry and "timestamp" in entry:
            # Using timestamp as x-value and responseTime as y-value
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
    # Create initial sample devices
    sample_devices = create_sample_devices()
    for device in sample_devices:
        DEVICES[device["id"]] = device
    logger.info(f"Created {len(sample_devices)} initial sample devices")
    app.run(host='0.0.0.0', port=5000, debug=True) 