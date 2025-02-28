import speech_recognition as sr
import pyttsx3
import datetime
import webbrowser
import os
import random
import json
import wikipedia
import requests
import subprocess
import time
import platform
import pytz
from newsapi import NewsApiClient  # pip install newsapi-python
import screen_brightness_control as sbc  # pip install screen-brightness-control
import pickle  

class VoiceAssistant:
    def __init__(self, name="Neura"):
        # Initialize the assistant
        self.name = name
        self.recognizer = sr.Recognizer()
        self.engine = pyttsx3.init()
        self.wake_word = name.lower()
        
        # Set voice properties
        voices = self.engine.getProperty('voices')
        self.engine.setProperty('voice', voices[1].id)  # Female voice
        self.engine.setProperty('rate', 180)  # Speed of speech
        
          # Initialize the news API client - you'll need to get an API key from newsapi.org
        self.news_api_key = "pub_721854cc9889ae3597d17a24772cfaa8e015d"  # Replace with your actual API key
        try:
            self.news_client = NewsApiClient(api_key=self.news_api_key)
        except:
            self.news_client = None
            
        # Weather API key - get from OpenWeatherMap
        self.weather_api_key = "c94d6753c91b8ec0bea1faea5591a2dc"  # Replace with your actual API key
        
        # Initialize reminders list and load any saved reminders
        self.reminders_file = "reminders.pkl"
        self.reminders = self.load_reminders()

        # Initialize commands dictionary - keep these simple for basic matching
        self.commands = {
            "hello": self.hello,
            "time": self.handle_time_request,
            "date": self.get_date,
            "search": self.search_web,
            "google": self.search_web,
            "open": self.open_application,
            "who is": self.wiki_search,
            "what is": self.handle_what_is,
            "weather": self.get_weather,  # New weather command
            "forecast": self.get_weather,  # Alternative weather command
            "news": self.get_news,  # New news command
            "headlines": self.get_news,  # Alternative news command
            "brightness": self.adjust_brightness,  # New display control
            "display": self.adjust_brightness,  # Alternative display control
            "screen": self.adjust_brightness,  # Alternative display control 
            "reminder": self.handle_reminder,  # New reminder command
            "remind": self.handle_reminder,  # Alternative reminder command
            "todo": self.handle_todo,  # New to-do command
            "task": self.handle_todo,  # Alternative to-do command
            "list": self.list_reminders,  # Command to list reminders
            "exit": self.exit_assistant,
            "goodbye": self.exit_assistant,
            "stop": self.exit_assistant
        }
        
        self.running = True
        self.active_mode = False
    
    def load_reminders(self):
        """Load reminders from file"""
        try:
            if os.path.exists(self.reminders_file):
                with open(self.reminders_file, 'rb') as f:
                    return pickle.load(f)
            return []
        except Exception as e:
            print(f"Error loading reminders: {e}")
            return []
    
    def save_reminders(self):
        """Save reminders to file"""
        try:
            with open(self.reminders_file, 'wb') as f:
                pickle.dump(self.reminders, f)
        except Exception as e:
            print(f"Error saving reminders: {e}")

    def speak(self, text):
        """Convert text to speech"""
        print(f"{self.name}: {text}")
        self.engine.say(text)
        self.engine.runAndWait()
        
    def listen(self, prompt=True):
        """Listen for user commands"""
        with sr.Microphone() as source:
            if prompt:
                print("Listening...")
            # Adjust for ambient noise
            self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
            try:
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=5)
                
                # Use Google's speech recognition
                command = self.recognizer.recognize_google(audio).lower()
                print(f"User: {command}")
                return command
            except sr.UnknownValueError:
                if prompt:
                    print("Sorry, I didn't understand that.")
                return ""
            except sr.RequestError:
                if prompt:
                    print("Speech service is currently unavailable.")
                return ""
            except:
                return ""
    
    def process_command(self, command):
        """Process the user's command with better natural language understanding"""
        # First, check for complex time queries with flexible phrasing
        if any(phrase in command for phrase in ["time in", "time at", "time it is in", "what time is it in", "what's the time in"]):
            self.get_time_zone(command)
            return True
            
        # Then check basic commands
        for key in self.commands:
            if key in command:
                self.commands[key](command)
                return True
                
        # If no command matches
        self.speak("I'm not sure how to help with that yet. Would you like me to search Google for this?")
        response = self.listen()
        if "yes" in response.lower() or "sure" in response.lower():
            self.search_web("search " + command)
        return True
    
    # Command functions
    def hello(self, command):
        """Greeting function"""
        responses = ["Hello! How can I help you?", 
                     "Hi there! What can I do for you?",
                     "Hey! How can I assist you today?"]
        self.speak(random.choice(responses))
    
    def handle_time_request(self, command):
        """General handler for time requests"""
        # Check if this is a time zone query
        if any(word in command for word in ["in", "at", "for"]):
            self.get_time_zone(command)
        else:
            # Just the local time
            self.get_time()
    
    def get_time(self):
        """Tell the current time"""
        current_time = datetime.datetime.now().strftime("%I:%M %p")
        self.speak(f"The current local time is {current_time}")
    
    def handle_what_is(self, command):
        """Handle 'what is' questions with smarter parsing"""
        # Check if it's a time query
        if "time" in command:
            self.handle_time_request(command)
        else:
            # Otherwise treat as a Wikipedia question
            self.wiki_search(command)
    
    def get_time_zone(self, command):
        """Get time for a specific timezone/city with flexible input handling"""
        # Extract the location name with more flexible pattern matching
        location = ""
        for pattern in ["time in", "time at", "time it is in", "time is in", "what time is it in", "what's the time in"]:
            if pattern in command:
                location = command.replace(pattern, "").strip().lower()
                break
                
        if not location:
            # Try one more method - look for the last word after "time"
            if "time" in command:
                parts = command.split("time")[1].strip().split()
                if parts:
                    # Get everything after any prepositions
                    for i, word in enumerate(parts):
                        if word in ["in", "at", "for"]:
                            location = " ".join(parts[i+1:])
                            break
        
        if not location:
            self.speak("Please specify a city or timezone.")
            return
            
        # Common city to timezone mapping
        timezone_map = {
            "london": "Europe/London",
            "new york": "America/New_York",
            "los angeles": "America/Los_Angeles",
            "paris": "Europe/Paris",
            "tokyo": "Asia/Tokyo",
            "sydney": "Australia/Sydney",
            "berlin": "Europe/Berlin",
            "moscow": "Europe/Moscow",
            "beijing": "Asia/Shanghai",
            "dubai": "Asia/Dubai",
            "mumbai": "Asia/Kolkata",
            "singapore": "Asia/Singapore",
            "toronto": "America/Toronto",
            "shanghai": "Asia/Shanghai",
            "sao paulo": "America/Sao_Paulo",
            "mexico city": "America/Mexico_City",
            "cairo": "Africa/Cairo",
            "johannesburg": "Africa/Johannesburg",
            "madrid": "Europe/Madrid",
            "rome": "Europe/Rome"
        }
        
        try:
            # Check if the location is in our map
            if location in timezone_map:
                tz = pytz.timezone(timezone_map[location])
                current_time = datetime.datetime.now(tz).strftime("%I:%M %p")
                self.speak(f"The current time in {location.title()} is {current_time}")
            else:
                # Try to use Google to get accurate time
                self.speak(f"I'll search for the current time in {location}")
                search_query = f"current time in {location}"
                url = f"https://www.google.com/search?q={search_query}"
                webbrowser.open(url)
                self.speak(f"I've opened a search for the current time in {location}")
        except Exception as e:
            self.speak(f"I'm having trouble finding the time for {location}. {str(e)}")
            self.search_web(f"search current time in {location}")
    
    def get_date(self, command):
        """Tell the current date"""
        current_date = datetime.datetime.now().strftime("%B %d, %Y")
        self.speak(f"Today is {current_date}")
 
    
    def search_web(self, command):
        """Search the web for a query"""
        if "google" in command:
            search_term = command.replace("google", "").strip()
        else:
            search_term = command.replace("search", "").strip()
            
        if search_term:
            url = f"https://www.google.com/search?q={search_term}"
            webbrowser.open(url)
            self.speak(f"Here's what I found for {search_term}")
        else:
            self.speak("What would you like me to search for?")
    
    def open_application(self, command):
        """Open an application"""
        app_name = command.replace("open", "").strip().lower()
        
        # Common applications dictionary with platform-specific commands
        windows_apps = {
            "notepad": "notepad.exe",
            "calculator": "calc.exe",
            "word": "winword.exe",
            "excel": "excel.exe",
            "powerpoint": "powerpnt.exe",
            "chrome": "chrome.exe",
            "firefox": "firefox.exe",
            "edge": "msedge.exe",
            "explorer": "explorer.exe",
            "paint": "mspaint.exe",
            "cmd": "cmd.exe",
            "control panel": "control.exe",
            "task manager": "taskmgr.exe",
            "settings": "ms-settings:",
            "vs code": "code.exe",
            "visual studio code": "code.exe",
            "note": "notepad.exe",
            "notes": "notepad.exe",
            "brave": "brave.exe",
            "clock": "clock.exe",
            "calendar": "outlookcal:",
            "copilot": "ms-copilot:",
            "whatsapp": "whatsapp.exe"

        }
        
        mac_apps = {
            "safari": "Safari",
            "chrome": "Google Chrome",
            "firefox": "Firefox",
            "terminal": "Terminal",
            "finder": "Finder",
            "calculator": "Calculator",
            "notes": "Notes",
            "note": "Notes",
            "calendar": "Calendar",
            "system preferences": "System Preferences",
            "music": "Music",
            "photos": "Photos",
            "vs code": "Visual Studio Code",
            "visual studio code": "Visual Studio Code",
            "whatsapp": "WhatsApp"
        }
        
        # Try to open the application based on the OS
        system = platform.system()
        self.speak(f"Trying to open {app_name}")
        
        try:
            if system == "Windows":
                # First check if it's in our known apps list
                if app_name in windows_apps:
                    app_path = windows_apps[app_name]
                    self.speak(f"Opening {app_name}")
                    subprocess.Popen(app_path, shell=True)
                else:
                    # Try to open it directly by name
                    self.speak(f"Attempting to open {app_name}")
                    subprocess.Popen(app_name, shell=True)
            
            elif system == "Darwin":  # macOS
                if app_name in mac_apps:
                    subprocess.Popen(["open", "-a", mac_apps[app_name]])
                    self.speak(f"Opening {app_name}")
                else:
                    # Try to open it directly by name
                    subprocess.Popen(["open", "-a", app_name])
                    self.speak(f"Attempting to open {app_name}")
            
            elif system == "Linux":
                # For Linux, try to open using the command directly
                subprocess.Popen([app_name])
                self.speak(f"Attempting to open {app_name}")
                
        except Exception as e:
            self.speak(f"I couldn't open {app_name}. The error was: {str(e)}")
    
    def wiki_search(self, command):
        """Search Wikipedia for information"""
        # Determine if it's "who is" or "what is"
        if "who is" in command:
            query = command.replace("who is", "").strip()
            self.speak(f"Searching for information about {query}")
        else:
            query = command.replace("what is", "").strip()
            self.speak(f"Searching for information about {query}")
        
        try:
            # Set language to English
            wikipedia.set_lang("en")
            
            # Get a summary from Wikipedia
            summary = wikipedia.summary(query, sentences=2)
            
            # Speak the summary
            self.speak(summary)
            
            # Offer to search the web for more info
            self.speak("Would you like me to search the web for more information?")
            response = self.listen()
            
            if "yes" in response.lower() or "sure" in response.lower() or "please" in response.lower():
                url = f"https://www.google.com/search?q={query}"
                webbrowser.open(url)
                self.speak(f"Here's what I found about {query}")
                
        except wikipedia.exceptions.DisambiguationError as e:
            # Handle disambiguation
            self.speak(f"There are multiple results for {query}. Please be more specific.")
            options = e.options[:5]  # Limit to first 5 options
            self.speak(f"Some options are: {', '.join(options)}")
            
        except wikipedia.exceptions.PageError:
            # Handle page not found
            self.speak(f"I couldn't find any information about {query} on Wikipedia.")
            self.speak("Would you like me to search the web instead?")
            response = self.listen()
            
            if "yes" in response.lower() or "sure" in response.lower():
                url = f"https://www.google.com/search?q={query}"
                webbrowser.open(url)
                self.speak(f"Here's what I found about {query}")
                
        except Exception as e:
            self.speak(f"I encountered an error while searching for {query}. {str(e)}")
    
    def get_weather(self, command):
        """Get weather information for a location"""
        # Extract location from command
        location = ""
        for pattern in ["weather in", "weather at", "weather for", "forecast in", "forecast at", "forecast for"]:
            if pattern in command:
                location = command.replace(pattern, "").strip()
                break
                
        if not location:
            self.speak("Which city would you like the weather for?")
            location = self.listen()
            
        if not location:
            self.speak("I couldn't understand the location. Please try again.")
            return
            
        try:
            # Make API request to OpenWeatherMap
            url = f"http://api.openweathermap.org/data/2.5/weather?q={location}&appid={self.weather_api_key}&units=metric"
            response = requests.get(url)
            data = response.json()
            
            if response.status_code == 200:
                # Extract relevant weather information
                temp = data['main']['temp']
                feels_like = data['main']['feels_like']
                condition = data['weather'][0]['description']
                humidity = data['main']['humidity']
                wind_speed = data['wind']['speed']
                
                # Provide weather information
                weather_info = (
                    f"The current weather in {location} is {condition} with a temperature of {temp:.1f}°C, "
                    f"feels like {feels_like:.1f}°C. "
                    f"Humidity is {humidity}% and wind speed is {wind_speed} meters per second."
                )
                self.speak(weather_info)
                
                # Offer forecast
                self.speak("Would you like a 5-day forecast?")
                response = self.listen()
                if "yes" in response.lower() or "sure" in response.lower():
                    forecast_url = f"http://api.openweathermap.org/data/2.5/forecast?q={location}&appid={self.weather_api_key}&units=metric"
                    webbrowser.open(forecast_url)
                    self.speak("I've opened a detailed forecast for you.")
            else:
                self.speak(f"I couldn't find weather information for {location}. Please check the city name and try again.")
                
        except Exception as e:
            self.speak(f"I encountered an error while getting weather information: {str(e)}")
            self.speak("Let me search for that information instead.")
            self.search_web(f"search weather in {location}")
    
    def get_news(self, command):
        """Get latest news headlines"""
        # Check if we have a valid news client
        if not self.news_client:
            self.speak("I'm sorry, but news functionality is not available at the moment. Please make sure you have a valid News API key.")
            return
            
        # Check for specific category or topic
        category = None
        topic = None
        
        # Extract category from command
        categories = ["business", "entertainment", "general", "health", "science", "sports", "technology"]
        for cat in categories:
            if cat in command:
                category = cat
                break
                
        # Extract topic from command
        for phrase in ["about", "on", "related to", "regarding"]:
            if phrase in command:
                parts = command.split(phrase, 1)
                if len(parts) > 1:
                    topic = parts[1].strip()
                    break
        
        try:
            if topic:
                # Get news on a specific topic
                self.speak(f"Getting the latest news about {topic}")
                news = self.news_client.get_everything(q=topic, language='en', sort_by='publishedAt', page_size=5)
            elif category:
                # Get news for a specific category
                self.speak(f"Getting the latest {category} news")
                news = self.news_client.get_top_headlines(category=category, language='en', page_size=5)
            else:
                # Get general top headlines
                self.speak("Getting the latest news headlines")
                news = self.news_client.get_top_headlines(language='en', country='us', page_size=5)
            
            # Process the results
            if news['status'] == 'ok' and news['totalResults'] > 0:
                articles = news['articles']
                self.speak(f"Here are the top {len(articles)} headlines:")
                
                for i, article in enumerate(articles, 1):
                    self.speak(f"Headline {i}: {article['title']}")
                    # Add a small pause between headlines
                    time.sleep(0.5)
                
                # Ask if user wants to open any of the articles
                self.speak("Would you like me to open any of these articles?")
                response = self.listen()
                
                if any(word in response.lower() for word in ["yes", "sure", "okay", "first", "1", "one"]):
                    # Default to first article if user just says yes
                    article_index = 0
                    
                    # Try to extract a number from the response
                    for word in response.split():
                        if word.isdigit() and 1 <= int(word) <= len(articles):
                            article_index = int(word) - 1
                            break
                    
                    # Open the article URL
                    article_url = articles[article_index]['url']
                    webbrowser.open(article_url)
                    self.speak("I've opened the article for you.")
            else:
                self.speak("I couldn't find any news articles at the moment.")
                
        except Exception as e:
            self.speak(f"I encountered an error while retrieving news: {str(e)}")
            self.speak("Let me search for news for you instead.")
            search_term = topic if topic else category if category else "latest news"
            self.search_web(f"search {search_term}")
    
    # NEW FEATURE: Display Control
    def adjust_brightness(self, command):
        """Adjust screen brightness"""
        try:
            # Check if a specific brightness value is mentioned
            value = None
            for word in command.split():
                if word.isdigit() and 0 <= int(word) <= 100:
                    value = int(word)
                    break
            
            # Look for percentage mentions
            if "%" in command:
                for word in command.split():
                    if "%" in word:
                        try:
                            value = int(word.replace("%", ""))
                            if 0 <= value <= 100:
                                break
                        except:
                            pass
            
            # Look for keywords
            if value is None:
                if any(word in command for word in ["maximum", "highest", "full", "brightest", "max"]):
                    value = 100
                elif any(word in command for word in ["minimum", "lowest", "dim", "dimmest", "min"]):
                    value = 10  # Not complete darkness for safety
                elif "half" in command or "medium" in command or "mid" in command:
                    value = 50
                elif "increase" in command or "up" in command or "higher" in command or "brighter" in command:
                    # Increase by 20%
                    current = sbc.get_brightness()[0]
                    value = min(current + 20, 100)
                elif "decrease" in command or "down" in command or "lower" in command or "dimmer" in command:
                    # Decrease by 20%
                    current = sbc.get_brightness()[0]
                    value = max(current - 20, 10)  # Not below 10% for safety
            
            # If we found a valid value, set the brightness
            if value is not None:
                sbc.set_brightness(value)
                self.speak(f"Screen brightness set to {value} percent")
            else:
                current = sbc.get_brightness()[0]
                self.speak(f"Current brightness is {current} percent. Please specify how you'd like to adjust it.")
                
        except Exception as e:
            self.speak(f"I couldn't adjust the brightness. The error was: {str(e)}")
            self.speak("This feature might not be supported on your system.")
    
    # NEW FEATURE: Personal Reminders & To-Do Lists
    def handle_reminder(self, command):
        """Set a reminder with time and message"""
        # Extract time and message from command
        time_phrases = ["at", "on", "for", "by"]
        
        # Default to setting a new reminder
        if "delete" in command or "remove" in command:
            self.delete_reminder(command)
            return
            
        # Set a new reminder
        time_str = None
        reminder_text = None
        
        # Extract potential time
        for phrase in time_phrases:
            if phrase + " " in command:
                parts = command.split(phrase + " ", 1)
                if len(parts) > 1:
                    possible_time = parts[1].split(" ", 1)
                    time_str = possible_time[0]
                    if len(possible_time) > 1:
                        reminder_text = possible_time[1]
                    else:
                        reminder_text = "reminder"
                    break
        
        # If no time was found in the command, ask for it
        if not time_str:
            # Extract the reminder text
            for start_phrase in ["remind me to", "remind me about", "reminder for", "reminder to"]:
                if start_phrase in command:
                    reminder_text = command.replace(start_phrase, "").strip()
                    break
            
            if not reminder_text:
                self.speak("What would you like me to remind you about?")
                reminder_text = self.listen()
                
            self.speak("When should I remind you? Please specify a time like '3pm' or a date like 'tomorrow at 2pm'.")
            time_str = self.listen()
        
        # Basic time processing
        if time_str and reminder_text:
            # Get current time
            now = datetime.datetime.now()
            
            # Create the reminder
            reminder = {
                "text": reminder_text,
                "time_str": time_str,
                "created": now.strftime("%Y-%m-%d %H:%M"),
                "status": "active"
            }
            
            # Add to reminders list
            self.reminders.append(reminder)
            self.save_reminders()
            
            self.speak(f"I've set a reminder for {time_str}: {reminder_text}")
            self.speak("I'll store this reminder, but please note that in this version I cannot send actual notifications when the time arrives.")
        else:
            self.speak("I couldn't understand the reminder details. Please try again with a clear time and message.")
    
    def delete_reminder(self, command):
        """Delete a reminder"""
        if not self.reminders:
            self.speak("You don't have any reminders set.")
            return
            
        # Try to extract which reminder to delete
        reminder_index = None
        reminder_text = None
        
        # Check for a number in the command
        for word in command.split():
            if word.isdigit() and 1 <= int(word) <= len(self.reminders):
                reminder_index = int(word) - 1
                break
        
        # Check for text match
        if reminder_index is None:
            self.speak("Which reminder would you like to delete? Please say the number or the content.")
            response = self.listen()
            
            # Check for number in response
            for word in response.split():
                if word.isdigit() and 1 <= int(word) <= len(self.reminders):
                    reminder_index = int(word) - 1
                    break
            
            # If still no index, try matching content
            if reminder_index is None:
                for i, reminder in enumerate(self.reminders):
                    if response.lower() in reminder["text"].lower():
                        reminder_index = i
                        break
        
        # Delete the reminder if found
        if reminder_index is not None:
            deleted_reminder = self.reminders.pop(reminder_index)
            self.save_reminders()
            self.speak(f"I've deleted the reminder: {deleted_reminder['text']}")
        else:
            self.speak("I couldn't identify which reminder to delete. Please try again.")
    
    def handle_todo(self, command):
        """Add a to-do item to the reminders list"""
        # Extract the task
        task = None
        for phrase in ["add to do", "add todo", "add to-do", "add task"]:
            if phrase in command:
                task = command.replace(phrase, "").strip()
                break
        
        if not task:
            self.speak("What task would you like to add to your to-do list?")
            task = self.listen()
        
        if task:
            # Create a to-do item (a reminder without a specific time)
            todo = {
                "text": task,
                "time_str": "anytime",
                "created": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                "status": "active",
                "type": "todo"
            }
            
            # Add to reminders list
            self.reminders.append(todo)
            self.save_reminders()
            
            self.speak(f"I've added '{task}' to your to-do list.")
        else:
            self.speak("I couldn't understand the task. Please try again.")
    
    def list_reminders(self, command):
        """List all reminders and to-dos"""
        if not self.reminders:
            self.speak("You don't have any reminders or to-do items.")
            return
        
        # Check if user wants to-dos or reminders specifically
        todos_only = any(phrase in command for phrase in ["todo list", "to do list", "to-do list", "tasks"])
        reminders_only = "reminders" in command
        
        # Filter based on request
        filtered_items = []
        if todos_only:
            filtered_items = [item for item in self.reminders if item.get("type") == "todo"]
            self.speak(f"You have {len(filtered_items)} items on your to-do list:")
        elif reminders_only:
            filtered_items = [item for item in self.reminders if item.get("type") != "todo"]
            self.speak(f"You have {len(filtered_items)} reminders:")
        else:
            filtered_items = self.reminders
            self.speak(f"You have {len(filtered_items)} reminders and to-do items:")
        
        # Speak all items
        for i, item in enumerate(filtered_items, 1):
            time_info = "" if item.get("time_str") == "anytime" else f" at {item['time_str']}"
            self.speak(f"Item {i}: {item['text']}{time_info}")
            # Add a small pause between items
            time.sleep(0.3)
    
    def exit_assistant(self, command):
        self.speak("Goodbye! Have a great day!")
        self.running = False
    
    def run(self):
        """Main loop for the assistant"""
        self.speak(f"Hello, I'm {self.name}. Say my name to wake me up.")
        
        while self.running:
            if not self.active_mode:
                # Listen for wake word
                print("Listening for wake word...")
                wake_command = self.listen(prompt=False)
                
                # Check if wake word is in the command
                if self.wake_word in wake_command.lower():
                    self.speak(f"Yes, I'm here. How can I help you?")
                    self.active_mode = True
            else:
                # Already in active mode, listen for commands directly
                print("I'm in active mode. Tell me what you need.")
                command = self.listen()
                
                if command:
                    # If the user says "sleep" or "go to sleep", exit active mode
                    if "sleep" in command.lower() or "go to sleep" in command.lower():
                        self.speak("I'll be here if you need me. Just say my name.")
                        self.active_mode = False
                    else:
                        # Process the command
                        self.process_command(command)
            
            # Small delay to prevent excessive CPU usage
            time.sleep(0.1)

if __name__ == "__main__":
    assistant = VoiceAssistant("Neura")  # Named Swift
    assistant.run()