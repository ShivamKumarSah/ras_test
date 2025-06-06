import pyttsx3
import datetime
import time
import requests
from typing import Dict, List, Optional
from flask import Flask, request, jsonify
from collections import Counter
import random
import logging
import json
import os
from flask_cors import CORS

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})  # Enable CORS for all API routes

# File paths for JSON storage
DEVICES_FILE = "devices.json"
COMMANDS_FILE = "commands.json"

# In-memory storage for devices and command history
DEVICES = {}
COMMAND_HISTORY = []

class Sheila:
    def __init__(self):
        self.engine = pyttsx3.init()
        self.engine.setProperty('voice', "HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Speech\\Voices\\Tokens\\TTS_MS_EN-US_ZIRA_11.0")
        self.engine.setProperty('rate', 150)
        self.engine.setProperty('volume', 1.0)
        self.weather_api_key = "11e3cf08706a5755f4cde00f819ad805"
        self.city = "Kolkata"  # Default city, you can change this or make it configurable
        
        # State management
        self.is_active = False
        self.current_device = None
        self.current_menu = None
        self.device_states = {
            'fan1': {'power': False, 'speed': 0},
            'fan2': {'power': False, 'speed': 0},
            'bulb1': {'power': False},
            'bulb2': {'power': False}
        }
        
        # Menu options
        self.main_menu = {
            '1': 'Control Fan 1',
            '2': 'Control Fan 2',
            '3': 'Control Bulb 1',
            '4': 'Control Bulb 2'
        }
        
        self.fan_menu = {
            'on': 'Start the fan',
            'off': 'Switch it off',
            '0': 'Level zero',
            '1': 'Level one',
            '2': 'Level two',
            '3': 'Level three',
            '4': 'Level four'
        }
        
        self.bulb_menu = {
            'on': 'Turn on the bulb',
            'off': 'Turn off the bulb'
        }

    def speak(self, text: str) -> None:
        """Convert text to speech"""
        self.engine.say(text)
        self.engine.runAndWait()

    def get_weather(self) -> str:
        """Get current weather information using OpenWeather API"""
        try:
            url = f"http://api.openweathermap.org/data/2.5/weather?q={self.city}&appid={self.weather_api_key}&units=metric"
            response = requests.get(url)
            data = response.json()
            
            if response.status_code == 200:
                temperature = round(data['main']['temp'])
                weather_description = data['weather'][0]['description']
                return f"{temperature}°C with {weather_description}"
            else:
                return "Unable to fetch weather information"
        except Exception as e:
            print(f"Error fetching weather: {str(e)}")
            return "Unable to fetch weather information"

    def get_greeting(self) -> str:
        """Get appropriate greeting based on time of day"""
        hour = datetime.datetime.now().hour
        if 5 <= hour < 12:
            return "Good morning"
        elif 12 <= hour < 17:
            return "Good afternoon"
        else:
            return "Good evening"

    def get_current_time(self) -> str:
        """Get current time in 12-hour format"""
        return datetime.datetime.now().strftime("%I:%M %p")

    def welcome_message(self, user_name: str = "User") -> None:
        """Display welcome message with time and weather"""
        greeting = self.get_greeting()
        current_time = self.get_current_time()
        weather = self.get_weather()
        
        message = f"{greeting}, {user_name}!I am your personal home assistant Sheila, The time is {current_time} and it's {weather}. What would you like to control today?"
        self.speak(message)
        time.sleep(2)
        self.speak("Would you like me to take you through the control menu?")
        self.current_menu = "welcome"

    def show_main_menu(self) -> None:
        """Display main control menu"""
        menu_text = "Here are your options:\n"
        for key, value in self.main_menu.items():
            menu_text += f"{key} for {value}\n"
        menu_text += "Please say the number of your choice."
        self.speak(menu_text)
        self.current_menu = "main"

    def show_device_menu(self, device_type: str) -> None:
        """Display device-specific control menu"""
        menu = self.fan_menu if 'fan' in device_type else self.bulb_menu
        menu_text = f"Here are your options for {device_type}:\n"
        for key, value in menu.items():
            menu_text += f"{key} for {value}\n"
        menu_text += "Please say your choice."
        self.speak(menu_text)
        self.current_menu = "device"
        self.current_device = device_type

    def process_device_command(self, device: str, command: str) -> None:
        """Process and execute device commands"""
        if 'fan' in device:
            if command.lower() == 'on':
                self.device_states[device]['power'] = True
                self.speak(f"{device} has been turned on")
            elif command.lower() == 'off':
                self.device_states[device]['power'] = False
                self.device_states[device]['speed'] = 0
                self.speak(f"{device} has been turned off")
            elif command.isdigit() and 0 <= int(command) <= 4:
                self.device_states[device]['speed'] = int(command)
                self.speak(f"{device} speed is now set to level {command} out of 4")
            else:
                self.handle_invalid_input()
        
        elif 'bulb' in device:
            if command.lower() == 'on':
                self.device_states[device]['power'] = True
                self.speak(f"{device} has been turned on")
            elif command.lower() == 'off':
                self.device_states[device]['power'] = False
                self.speak(f"{device} has been turned off")
            else:
                self.handle_invalid_input()

    def handle_invalid_input(self) -> None:
        """Handle invalid user input by repeating the current menu"""
        self.speak("The input command is invalid.")
        time.sleep(1)
        
        if self.current_menu == "welcome":
            self.speak("Please say 'yes' if you want to see the control menu, or 'no' to exit.")
        elif self.current_menu == "main":
            self.show_main_menu()
        elif self.current_menu == "device":
            self.show_device_menu(self.current_device)
        else:
            self.speak("Please try again with a valid command.")

    def run(self) -> None:
        """Main interaction loop"""
        self.is_active = True
        self.welcome_message()
        
        while self.is_active:
            # TODO: Implement voice recognition here
            # For now, we'll simulate user input
            user_input = input("Your command: ").lower().strip()
            
            if self.current_menu == "welcome":
                if user_input == 'yes':
                    self.show_main_menu()
                elif user_input == 'no':
                    self.speak("Thanks for interacting with me. Just call me when you need my service.")
                    self.is_active = False
                else:
                    self.handle_invalid_input()
            
            elif self.current_menu == "main":
                if user_input in self.main_menu:
                    device = f"fan{user_input}" if user_input in ['1', '2'] else f"bulb{int(user_input)-2}"
                    self.speak(f"You chose {self.main_menu[user_input]}. What do you want to do with it?")
                    time.sleep(2)
                    self.speak("Would you like me to take you through the control menu?")
                    self.current_menu = "device_choice"
                else:
                    self.handle_invalid_input()
            
            elif self.current_menu == "device_choice":
                if user_input == 'yes':
                    self.show_device_menu(device)
                elif user_input == 'no':
                    self.speak("Thanks for interacting with me. Just call me when you need my service.")
                    self.is_active = False
                else:
                    self.handle_invalid_input()
            
            elif self.current_menu == "device":
                self.process_device_command(device, user_input)
                self.speak("Anything else?")
                if input("Continue? (yes/no): ").lower() == 'no':
                    self.speak("Thanks for interacting with me. Just call me when you need my service.")
                    self.is_active = False
                else:
                    self.show_main_menu()

def load_json_file(filename, default_value):
    """Load data from JSON file or return default value if file doesn't exist"""
    try:
        if os.path.exists(filename):
            with open(filename, 'r') as f:
                return json.load(f)
        return default_value
    except Exception as e:
        logger.error(f"Error loading {filename}: {str(e)}")
        return default_value

def save_json_file(filename, data):
    """Save data to JSON file"""
    try:
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        logger.error(f"Error saving {filename}: {str(e)}")

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
            # Save to JSON file
            save_json_file(DEVICES_FILE, DEVICES)
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
        # Save to JSON file
        save_json_file(DEVICES_FILE, DEVICES)
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
    # Save to JSON file
    save_json_file(DEVICES_FILE, DEVICES)
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
    
    # Save to JSON file
    save_json_file(DEVICES_FILE, DEVICES)
    
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
    Process command and return a result.
    """
    start_time = time.time() # Record start time
    data = request.get_json() or {}
    cmd = data.get('cmd', '').strip()

    if not cmd:
        return jsonify({ "status": "error", "result": "No command provided." }), 400

    # Process command (this will be integrated with Sheila's voice processing)
    # For now, we'll simulate processing
    simulated_latency = random.uniform(50, 500) # Simulate processing time
    time.sleep(simulated_latency / 1000) # Simulate blocking I/O
    end_time = time.time() # Record end time
    response_time_ms = round((end_time - start_time) * 1000)

    result_text = f"Executed command: {cmd}"
    status = "success"

    # Record into history
    command_entry = {
        "cmd": cmd,
        "status": status,
        "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "responseTime": response_time_ms,
        "user": "default_user",
        "response": result_text,
        "result": result_text
    }
    
    COMMAND_HISTORY.append(command_entry)
    # Save to JSON file
    save_json_file(COMMANDS_FILE, COMMAND_HISTORY)

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
    
    # Load existing data from JSON files
    DEVICES = load_json_file(DEVICES_FILE, {})
    COMMAND_HISTORY = load_json_file(COMMANDS_FILE, [])
    
    # Create initial sample devices if none exist
    if not DEVICES:
        sample_devices = create_sample_devices()
        for device in sample_devices:
            DEVICES[device["id"]] = device
        save_json_file(DEVICES_FILE, DEVICES)
        logger.info(f"Created {len(sample_devices)} initial sample devices")
    
    app.run(host='0.0.0.0', port=5000, debug=True)
