import pyttsx3
import datetime
import time
import requests
from typing import Dict, List, Optional

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

if __name__ == "__main__":
    sheila = Sheila()
    sheila.run()
