import pyttsx3
import datetime
import time
import requests
import speech_recognition as sr
import json
import os

class Sheila:
    def __init__(self):
        self.engine = pyttsx3.init()
        self.engine.setProperty('voice', "HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Speech\\Voices\\Tokens\\TTS_MS_EN-US_ZIRA_11.0")
        self.engine.setProperty('rate', 150)
        self.engine.setProperty('volume', 1.0)
        self.weather_api_key = "11e3cf08706a5755f4cde00f819ad805"
        self.city = "Kolkata"
        self.is_active = False
        self.current_device = None
        self.current_menu = None
        self.commands_file = "commands.json"
        self.devices_file = "devices.json"
        
        # Number word mapping
        self.number_words = {
            'zero': '0', 'one': '1', 'two': '2', 'three': '3', 'four': '4',
            'first': '1', 'second': '2', 'third': '3', 'fourth': '4',
            '1st': '1', '2nd': '2', '3rd': '3', '4th': '4'
        }
        
        # Initialize device states with actual device IDs
        self.device_states = {
            'fan1': {'power': False, 'speed': 0},
            'fan2': {'power': False, 'speed': 0},
            'bulb1': {'power': False},
            'bulb2': {'power': False}
        }
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
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        with self.microphone as source:
            print("Microphone ready!")

    def normalize_command(self, command: str) -> str:
        """Convert word numbers to digits and normalize command"""
        command = command.lower().strip()
        words = command.split()
        normalized_words = [self.number_words.get(word, word) for word in words]
        return ' '.join(normalized_words)

    def speak(self, text: str) -> None:
        print(f"Sheila: {text}")
        self.engine.say(text)
        self.engine.runAndWait()

    def get_weather(self) -> str:
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
            return "Unable to fetch weather information"

    def get_greeting(self) -> str:
        hour = datetime.datetime.now().hour
        if 5 <= hour < 12:
            return "Good morning"
        elif 12 <= hour < 17:
            return "Good afternoon"
        else:
            return "Good evening"

    def get_current_time(self) -> str:
        return datetime.datetime.now().strftime("%I:%M %p")

    def listen(self, prompt=None, retries=3) -> str:
        self.command_start_time = time.time()
        for attempt in range(retries):
            if prompt:
                self.speak(prompt)
            with self.microphone as source:
                print("Listening...")
                try:
                    audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=7)
                    text = self.recognizer.recognize_google(audio).lower()
                    print(f"You said: {text}")
                    normalized_text = self.normalize_command(text)
                    # Store successful command
                    self.store_command(text, f"Executed command: {text}")
                    return normalized_text
                except sr.UnknownValueError:
                    self.speak("Sorry, I didn't catch that. Please repeat.")
                    self.store_command("", "Speech not recognized", "failed")
                except sr.WaitTimeoutError:
                    self.speak("I didn't hear anything. Please try again.")
                    self.store_command("", "No speech detected", "failed")
                except sr.RequestError as e:
                    self.speak(f"Speech recognition error: {e}")
                    self.store_command("", f"Speech recognition error: {e}", "failed")
                    break
                except Exception as e:
                    self.speak(f"Error: {e}")
                    self.store_command("", f"Error: {e}", "failed")
        return ""

    def update_device_state(self, device_id: str, updates: dict) -> None:
        """Update device state in devices.json"""
        try:
            with open(self.devices_file, 'r') as f:
                devices = json.load(f)
            
            if device_id in devices:
                devices[device_id].update(updates)
                devices[device_id]['lastUpdated'] = datetime.datetime.utcnow().isoformat()
                
                with open(self.devices_file, 'w') as f:
                    json.dump(devices, f, indent=2)
        except Exception as e:
            print(f"Error updating device state: {str(e)}")

    def store_command(self, command: str, response: str, status: str = "success") -> None:
        """Store command in commands.json with actual response time"""
        try:
            if os.path.exists(self.commands_file):
                with open(self.commands_file, 'r') as f:
                    commands = json.load(f)
            else:
                commands = []

            response_time = int((time.time() - self.command_start_time) * 1000)
            command_entry = {
                "cmd": command,
                "status": status,
                "timestamp": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
                "responseTime": response_time,
                "user": "default_user",
                "response": response,
                "result": response
            }

            commands.append(command_entry)

            with open(self.commands_file, 'w') as f:
                json.dump(commands, f, indent=2)

        except Exception as e:
            print(f"Error storing command: {str(e)}")

    def process_device_command(self, device: str, command: str) -> None:
        command = command.lower().strip()
        device_map = {
            '1': 'fan1',
            '2': 'fan2',
            '3': 'bulb1',
            '4': 'bulb2'
        }
        device_id = device_map.get(device, device)

        if 'fan' in device_id:
            if command == 'on':
                self.device_states[device_id]['power'] = True
                self.update_device_state(device_id, {'isOn': True})
                self.speak(f"{device_id} has been turned on")
            elif command == 'off':
                self.device_states[device_id]['power'] = False
                self.device_states[device_id]['speed'] = 0
                self.update_device_state(device_id, {'isOn': False, 'speed': 0})
                self.speak(f"{device_id} has been turned off")
            elif command in ['0', '1', '2', '3', '4'] or command in self.number_words.values():
                speed = command if command in ['0', '1', '2', '3', '4'] else self.number_words.get(command, command)
                self.device_states[device_id]['speed'] = int(speed)
                self.update_device_state(device_id, {'speed': int(speed)})
                self.speak(f"{device_id} speed is now set to level {speed} out of 4")
            else:
                self.handle_invalid_input()
        elif 'bulb' in device_id:
            if command == 'on':
                self.device_states[device_id]['power'] = True
                self.update_device_state(device_id, {'isOn': True})
                self.speak(f"{device_id} has been turned on")
            elif command == 'off':
                self.device_states[device_id]['power'] = False
                self.update_device_state(device_id, {'isOn': False})
                self.speak(f"{device_id} has been turned off")
            else:
                self.handle_invalid_input()

    def handle_invalid_input(self) -> None:
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

    def welcome_message(self, user_name: str = "User") -> None:
        greeting = self.get_greeting()
        current_time = self.get_current_time()
        weather = self.get_weather()
        message = f"{greeting}, {user_name}! I am your personal home assistant Sheila. The time is {current_time} and it's {weather}. What would you like to control today?"
        self.speak(message)
        time.sleep(2)
        # self.speak("Would you like me to take you through the control menu?")
        self.current_menu = "welcome"

    def show_main_menu(self) -> None:
        menu_text = "Here are your options: "
        for key, value in self.main_menu.items():
            menu_text += f"{key} for {value}, "
        menu_text += "Please say the number of your choice."
        self.speak(menu_text)
        self.current_menu = "main"

    def show_device_menu(self, device_type: str) -> None:
        menu = self.fan_menu if 'fan' in device_type else self.bulb_menu
        menu_text = f"Here are your options for {device_type}: "
        for key, value in menu.items():
            menu_text += f"{key} for {value}, "
        menu_text += "Please say your choice."
        self.speak(menu_text)
        self.current_menu = "device"
        self.current_device = device_type

    def run(self) -> None:
        self.is_active = True
        print("\nSheila is listening! Say 'Sheila' or 'Sheela' to activate.")
        while self.is_active:
            text = self.listen(prompt=None, retries=3)
            if not text:
                continue
            if "sheila" in text or "sheela" in text:
                self.welcome_message()
                while self.is_active:
                    if self.current_menu == "welcome":
                        command = self.listen("Say 'yes' for menu or 'no' to exit.")
                        if 'yes' in command:
                            self.show_main_menu()
                        elif 'no' in command:
                            self.speak("Thanks for interacting with me. Just call me when you need my service.")
                            self.is_active = False
                            break
                        else:
                            self.handle_invalid_input()
                    elif self.current_menu == "main":
                        command = self.listen("Please say the number of your choice.")
                        command = self.normalize_command(command)
                        if command in self.main_menu:
                            device = command
                            self.speak(f"You chose {self.main_menu[command]}. What do you want to do with it?")
                            time.sleep(2)
                            self.speak("Would you like me to take you through the control menu?")
                            self.current_menu = "device_choice"
                            self.current_device = device
                        else:
                            self.handle_invalid_input()
                    elif self.current_menu == "device_choice":
                        command = self.listen("Say 'yes' for device menu or 'no' to exit.")
                        if 'yes' in command:
                            self.show_device_menu(self.current_device)
                        elif 'no' in command:
                            self.speak("Thanks for interacting with me. Just call me when you need my service.")
                            self.is_active = False
                            break
                        else:
                            self.handle_invalid_input()
                    elif self.current_menu == "device":
                        command = self.listen("Please say your command for the device.")
                        self.process_device_command(self.current_device, command)
                        self.speak("Anything else? Say 'yes' to continue or 'no' to exit.")
                        cont = self.listen()
                        if 'no' in cont:
                            self.speak("Thanks for interacting with me. Just call me when you need my service.")
                            self.is_active = False
                            break
                        else:
                            self.show_main_menu()

if __name__ == "__main__":
    sheila = Sheila()
    sheila.run() 