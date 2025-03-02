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
import socket  # For IP address functions
import requests  # For web API calls
import string
import re
import numpy as np
from forex_python.converter import CurrencyRates
import google.generativeai as genai
from typing import Optional

class VoiceAssistant:
    def __init__(self, name="Neura"):
        # Initialize the assistant
        self.name = name
        self.recognizer = sr.Recognizer()
        self.engine = pyttsx3.init()
        self.wake_word = name.lower()

        # Add this to your VoiceAssistant's _init_ method
        self.gemini_api_key = "AIzaSyBiTh7z33wRmEh2aheBvx6PtowCbeKt4Ug"   # Replace with your actual API  key
        try:
            genai.configure(api_key=self.gemini_api_key)
            self.gemini_model = genai.GenerativeModel('gemini-2.0-flash')
        except Exception as e:
                print(f"Error initializing Gemini API: {e}")
                self.gemini_model = None
        
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
            "owner": self.about_developer,
            "krish": self.about_developer,
            "krrish ": self.about_developer,
            "my name": self.about_developer,
            "who made you": self.about_developer,
            "who created you": self.about_developer,
            "who is your developer": self.about_developer,
            "who is your creator": self.about_developer,
            "hello": self.hello,
            "time": self.handle_time_request,
            "date": self.get_date,
            "search": self.search_web,
            "google": self.search_web,
            "open": self.open_application,
            "who is": self.wiki_search,
            "what is": self.handle_what_is,
            "what can you do": self.show_capabilities,
            "help": self.show_capabilities,
            "capabilities": self.show_capabilities,
            "features": self.show_capabilities,
            "commands": self.show_capabilities,
            "menu": self.show_capabilities,
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
            "stop": self.exit_assistant,

            "check internet speed": self.check_speed,
            "internet speed": self.check_speed,
            "speed test": self.check_speed,
            "what is my ip": self.get_ip_address,
            "my ip": self.get_ip_address,
            "ip address": self.get_ip_address,
            "ping": self.ping_website,
            "open website": self.open_website,
            "go to": self.open_website,
            "visit": self.open_website,
            "show calendar": self.show_calendar,
            "calendar": self.show_calendar,
            "translate": self.translate_text,
            "define": self.dictionary_lookup,
            "meaning of": self.dictionary_lookup,
            "tell me a joke": self.tell_joke,
            "joke": self.tell_joke,
            "motivate me": self.get_motivational_quote,
            "inspire me": self.get_motivational_quote,
            "quote": self.get_motivational_quote,
            "search files": self.search_files,
            "find files": self.search_files,
            "password": self.handle_password,
            "generate password": self.generate_password,
            "check password": self.check_password_strength,
            "convert currency": self.convert_currency,
            "exchange rate": self.convert_currency,
            "currency": self.convert_currency,
            "generate code": self.generate_code,
            "write code": self.generate_code,
            "code for": self.generate_code,
            "implement": self.generate_code,
        }
        
        self.running = True
        self.active_mode = False
    
    

    def about_developer(self, command):
        """Provide information about the developer"""
        developer_info = (
        "My developer is Krrish, a 2nd year student at CU pursuing AIML. "
        "He created me as a voice assistant project to demonstrate his programming skills "
        "and knowledge of artificial intelligence. Krrish is passionate about AI development "
        "and aspires to work on advanced AI systems in the future. "
        "He has invested significant time in designing my features to make me helpful and responsive."
    )

        self.speak(developer_info)
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
            "chrome": "C:\Program Files\Google\Chrome\Application\chrome.exe",
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
    
    def show_capabilities(self, command):
    
        capabilities = {
        "Time and Date": ["Get current time", "Get time in different cities", "Get current date"],
        "Information": ["Search the web", "Find information on Wikipedia", "Get weather updates", "Get latest news"],
        "System Control": ["Open applications", "Adjust screen brightness", "Control system settings"],
        "Personal Management": ["Set reminders", "Manage to-do lists", "Create tasks"],
        "Other Features": ["Exit the assistant"]
        }

        self.speak("Here are the things I can help you with:")

    # List all capabilities
        for category, features in capabilities.items():
            self.speak(f"{category}:")
        for feature in features:
            self.speak(f"- {feature}")
        time.sleep(0.5)  # Small pause

        self.speak("You can ask me to do any of these tasks. What would you like me to do?")
    
        category_response = self.listen()
        selected_category = None

        # Try to match by number first
        for word in category_response.split():
            if word.isdigit() and 1 <= int(word) <= len(capabilities):
                selected_category = list(capabilities.keys())[int(word)-1]
            break

        # If no match by number, try matching by name
        if not selected_category:
            for category in capabilities.keys():
             if category.lower() in category_response.lower():
                selected_category = category
                break

    # If still no match, list all capabilities again
        if not selected_category:
            self.speak("I'm not sure which category you meant. Here are all my capabilities again:")
            for category, features in capabilities.items():
             self.speak(f"{category}:")
            for feature in features:
                    self.speak(f"- {feature}")
                    time.sleep(0.3)
            return

        # Show features for the selected category
        self.speak(f"Here's what I can do with {selected_category}:")
        for i, feature in enumerate(capabilities[selected_category], 1):
            self.speak(f"{i}. {feature}")

        # Ask if user wants to try one of these features
        self.speak("Would you like to try any of these features now? If so, which one?")
        feature_response = self.listen()

        # Map general feature descriptions to command keywords
        feature_to_command = {
            "current time": "time",
            "time in different": "time in",
            "current date": "date",
            "search the web": "search",
            "wikipedia": "what is",
            "weather": "weather",
            "news": "news",
            "open application": "open",
            "brightness": "brightness",
            "reminder": "reminder",
            "to-do": "todo",
            "task": "task",
            "exit": "exit"
        }

        # Try to identify which feature the user wants to try
        selected_command = None

        # Check for direct feature mention
        for feature_key, command in feature_to_command.items():
            if feature_key.lower() in feature_response.lower():
                selected_command = command
                break

        # If no direct match, try to match by feature number within the category
        if not selected_command:
            for word in feature_response.split():
                if word.isdigit() and 1 <= int(word) <= len(capabilities[selected_category]):
                    feature_text = capabilities[selected_category][int(word)-1].lower()
                    # Find the closest command match
                    for feature_key, command in feature_to_command.items():
                        if feature_key.lower() in feature_text:
                            selected_command = command
                            break
                    if selected_command:
                        break

        # Execute the selected command if found
        if selected_command:
            self.speak(f"I'll help you with that. What specifically would you like to know about {selected_command}?")
            specific_response = self.listen()

            # Combine the command with the specific request
            full_command = f"{selected_command} {specific_response}"
            self.process_command(full_command)
        else:
            self.speak("I'm not sure which feature you want to try. Please ask me directly when you're ready.")

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

    def check_speed(self, command):
        """Check internet speed using speedtest-cli"""
        self.speak("Running an internet speed test. This might take a few moments...")
        try:
            # Use subprocess to run the speedtest-cli tool
            self.speak("Opening the speed test website for you.")
            webbrowser.open("https://www.speedtest.net/")
            return True
        except Exception as e:
            self.speak(f"I encountered an error while checking internet speed: {str(e)}")
            return False
        
    def get_ip_address(self, command):
        """Get the public and local IP address"""
        try:
            # Get public IP
            self.speak("Retrieving your IP address information...")
            response = requests.get("https://api.ipify.org?format=json")
            public_ip = response.json()["ip"]

            # Get local IP
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)

            self.speak(f"Your public IP address is {public_ip}")
            self.speak(f"Your local IP address is {local_ip}")
            return True
        except Exception as e:
            self.speak(f"I encountered an error while retrieving your IP: {str(e)}")
            return False
        
    def ping_website(self, command):
        """Ping a website to check connectivity"""
        # Extract website from command
        website = None
        if "ping" in command:
            website = command.replace("ping", "").strip()

        if not website:
            self.speak("Which website would you like to ping?")
            website = self.listen()

        if website:
            self.speak(f"Pinging {website}. Please wait...")
            try:
                # Use subprocess to run ping command
                process = subprocess.Popen(
                    ["ping", "-n", "4", website],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                output, error = process.communicate()

                if error:
                    self.speak(f"Error while pinging {website}: {error}")
                else:
                    # Extract average time from output
                    if "Average" in output:
                        avg_time = output.split("Average = ")[1].split("ms")[0]
                        self.speak(f"Ping to {website} was successful with an average time of {avg_time} milliseconds.")
                    else:
                        self.speak(f"Ping to {website} completed. {website} is reachable.")
                return True
            except Exception as e:
                self.speak(f"I couldn't ping {website}. Error: {str(e)}")
                return False
            
    def open_website(self, command):
        """Open a website in the default browser"""
        # Extract URL from command
        url = None
        for phrase in ["open website", "go to", "visit"]:
            if phrase in command:
                url = command.replace(phrase, "").strip()
                break
            
        if not url:
            self.speak("Which website would you like to open?")
            url = self.listen()

        if url:
            # Add http:// if not present
            if not url.startswith("http"):
                url = "https://" + url

            # Add .com if no domain extension
            if "." not in url.split("//")[1]:
                url = url + ".com"

            try:
                self.speak(f"Opening {url}")
                webbrowser.open(url)
                return True
            except Exception as e:
                self.speak(f"I couldn't open {url}. Error: {str(e)}")
                return False
    
    def show_calendar(self, command):
        """Show calendar application or current month"""
        self.speak("Opening calendar.")
        try:
            # For Windows, open the built-in Calendar app
            subprocess.Popen("explorer.exe shell:AppsFolder\\microsoft.windowscommunicationsapps_8wekyb3d8bbwe!microsoft.windowslive.calendar")
            return True
        except Exception as e:
            # Fallback to web calendar
            self.speak("I couldn't open your calendar app. Opening web calendar instead.")
            webbrowser.open("https://calendar.google.com")
            return True
        
    def translate_text(self, command):
        """Translate text from one language to another"""
        # Extract text and languages
        text_to_translate = None
        target_language = "english"  # Default

        if "translate" in command:
            parts = command.replace("translate", "").strip().split(" to ")
            if len(parts) >= 1:
                text_to_translate = parts[0].strip()
                if len(parts) >= 2:
                    target_language = parts[1].strip()

        if not text_to_translate:
            self.speak("What would you like me to translate?")
            text_to_translate = self.listen()

            if text_to_translate:
                self.speak("To which language? Say 'to' followed by the language name.")
                lang_response = self.listen()
                if "to" in lang_response:
                    target_language = lang_response.split("to")[1].strip()

        if text_to_translate:
            self.speak(f"Translating '{text_to_translate}' to {target_language}")
            # Open Google Translate with the text
            encoded_text = requests.utils.quote(text_to_translate)
            encoded_lang = requests.utils.quote(target_language)
            url = f"https://translate.google.com/?sl=auto&tl={encoded_lang}&text={encoded_text}&op=translate"
            webbrowser.open(url)
            return True
        else:
            self.speak("I couldn't understand what to translate.")
            return False
        
    def dictionary_lookup(self, command):
        """Look up the definition of a word"""
        # Extract word from command
        word = None
        for phrase in ["define", "meaning of"]:
            if phrase in command:
                word = command.replace(phrase, "").strip()
                break
            
        if not word:
            self.speak("Which word would you like me to define?")
            word = self.listen()

        if word:
            self.speak(f"Looking up the definition of {word}")
            try:
                # Using free dictionary API
                response = requests.get(f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}")
                if response.status_code == 200:
                    data = response.json()
                    definition = data[0]["meanings"][0]["definitions"][0]["definition"]
                    part_of_speech = data[0]["meanings"][0]["partOfSpeech"]
                    self.speak(f"{word} is a {part_of_speech}.")
                    self.speak(f"Definition: {definition}")

                    # Check if there are examples
                    if "example" in data[0]["meanings"][0]["definitions"][0]:
                        example = data[0]["meanings"][0]["definitions"][0]["example"]
                        self.speak(f"Example: {example}")
                    return True
                else:
                    self.speak(f"I couldn't find a definition for {word}. Opening an online dictionary instead.")
                    webbrowser.open(f"https://www.dictionary.com/browse/{word}")
                    return True
            except Exception as e:
                self.speak(f"I encountered an error looking up that word: {str(e)}")
                self.speak(f"Opening an online dictionary for {word} instead.")
                webbrowser.open(f"https://www.dictionary.com/browse/{word}")
                return True
            
    def tell_joke(self, command):
        """Tell a random joke"""
        jokes = [
            # Funny Hindi Jokes
            "Teacher: Bachho koi aisa vaakya batao jisme 'lekin' shabd do baar aaye!\nGolu: Main school to roj jata hoon lekin... lekin chhutti ke din nahi!",
            "Doctor: Jab tumhe pareshani hoti hai to tum kya karte ho?\nPappu: Ji mandir chala jata hoon!\nDoctor: Bahut achha karte ho, dhyan lagate ho na wahan?\nPappu: Nahi ji… wahan se wife ko call karta hoon, network jo pura aata hai!",
            "Santa: Agar meri shaadi ho gayi to main biwi ko Paris ghumane le jaunga.\nBanta: Aur agar shaadi nahi hui to?\nSanta: To Paris hi chala jaunga!",
            "Patni (gusse me): Shaadi se pehle tum mujhe hotel, cinema, shopping karate the, aur ab?\nPati: Kabhi suna hai – 'Vote maangne se pehle neta haath jodta hai, aur baad me janta!'",
            "Teacher: Bachho, samajhdari kise kehte hain?\nGolu: Master ji, shaadi se pehle pyaar karna aur shaadi ke baad pyaar ko samajhdari se nibhana!",
            "Teacher: Ek taraf paisa, doosri taraf akal, tum kya chuno ge?\nGolu: Paisa!\nTeacher: Galat, main akal chunati!\nGolu: Theek hai madam, jo cheez jiske paas nahi hoti, wahi wo chunta hai!",
            "Pappu bank gaya aur manager se bola: 'Mujhe loan chahiye!'\nManager: 'Kis liye?'\nPappu: 'Ji shaadi ke liye.'\nManager: 'Lekin shaadi ke liye to loan nahi milta!'\nPappu: 'To fir kya karein? Loan le kar ladki bhaga lein?'",
            "Santa doctor se: 'Doctor sahab, jab main sota hoon to sapne me chuhe football khelte hain.'\nDoctor: 'Ye lo dawai raat ko sone se pehle kha lena.'\nSanta: 'Kal se kha loonga doctor sahab, aaj to final match hai!'",
            "Patni: Tum mujhe koi gift nahi dete, na shopping karate ho!\nPati: Are pagli, Facebook aur Instagram pe dil aur likes bhejta hoon na!",
            "Golu teacher se: 'Madam, aap shaadishuda ho?'\nTeacher: 'Nahi, par kyu pooch rahe ho?'\nGolu: 'Kyunki aapki shakal meri mummy se milti hai, aur mummy kehti hain ki papa se shaadi karke unki zindagi kharab ho gayi!'",

            # Adult (18+) Jokes
            "Pati apni patni se: Suno, aaj raat hum role-play karein?\nPatni: Haan haan, chalo doctor aur patient wala khelte hain!\nPati: Achha theek hai, to meri appointment kal ki hai!",
            "Santa (girlfriend se): Tumhare papa mujhse nafrat kyu karte hain?\nGirlfriend: Kyunki tumne pehli mulaqat me hi unhe 'daddy' bol diya tha!",
            "Patni: Raat ko kahan ja rahe ho?\nPati: Cigarette lene!\nPatni: Are, yeh to shaadi se pehle peete the na?\nPati: Haan, shaadi se pehle pyaar bhi to karte the!",
            "Teacher: Ek aisa vaakya batao jisme 'sambhavana' shabd aaye!\nBaccha: Raat ko mummy papa ke kamre se awaaz aayi: ‘Sambhavana hai ki beta ho!’",
            "Girlfriend: Tumhe mujhse kitna pyaar hai?\nBoyfriend: Utna hi jitna prepaid user ko raat me free data se hota hai!",
            "Patni: Shaadi se pehle tum mere liye kuch bhi kar sakte the, ab?\nPati: Ab to insurance kara liya hai, thoda sabr kar lo!",
            "Pati: Tum humesha ladayi kyu karti ho?\nPatni: Kyunki tum meri feelings ko samajhte nahi ho!\nPati: Achha, to WhatsApp status pe daal deti na!",
            "Pati: Tum itni sundar kyu lag rahi ho aaj?\nPatni (sharmate hue): Sach me?\nPati: Haan, aur jaldi se batao paise kitne kharch kiye!",
            "Santa bathroom me gaya aur chillaya: ‘Are koi hai?’\nPatni daudti aayi: ‘Kya hua?’\nSanta: ‘Kuch nahi, bas dekh raha tha, sach me koi meri parwah karta hai ya nahi!’",
            "Boyfriend: Janu, tum itni sundar kaise dikh rahi ho?\nGirlfriend: Makeup aur filter se!\nBoyfriend: Are haan, jabse tum aayi ho, mera phone hang ho gaya!"
        ]

        joke = random.choice(jokes)
        self.speak(joke)
        return True
    
    def get_motivational_quote(self, command):
        """Share a motivational or inspirational quote"""
        quotes = [
            "The only way to do great work is to love what you do. - Steve Jobs",
            "Believe you can and you're halfway there. - Theodore Roosevelt",
            "It does not matter how slowly you go as long as you do not stop. - Confucius",
            "Everything you've ever wanted is on the other side of fear. - George Addair",
            "Success is not final, failure is not fatal: It is the courage to continue that counts. - Winston Churchill",
            "Hardships often prepare ordinary people for an extraordinary destiny. - C.S. Lewis",
            "Your time is limited, don't waste it living someone else's life. - Steve Jobs",
            "The future belongs to those who believe in the beauty of their dreams. - Eleanor Roosevelt",
            "You are never too old to set another goal or to dream a new dream. - C.S. Lewis",
            "The only limit to our realization of tomorrow will be our doubts of today. - Franklin D. Roosevelt"
        ]

        quote = random.choice(quotes)
        self.speak(quote)
        return True
    
    def search_files(self, command):
        """Search for files on the computer"""
        # Extract file type or name from command
        file_query = None
        for phrase in ["search files", "find files"]:
            if phrase in command:
                file_query = command.replace(phrase, "").strip()
                break
            
        if not file_query:
            self.speak("What type of files would you like me to search for?")
            file_query = self.listen()

        if file_query:
            self.speak(f"Searching for {file_query} files on your computer")

            # Determine search approach based on query
            if file_query.startswith("."):
                # This is a file extension search (e.g., ".pdf")
                search_term = file_query
            else:
                # This is a keyword search
                if not file_query.endswith("files"):
                    search_term = file_query + " files"
                else:
                    search_term = file_query

            # Open Windows Explorer with search
            search_command = f'explorer.exe search-ms:query={search_term}&crumb=location:%3A'
            subprocess.Popen(search_command, shell=True)
            return True
        else:
            self.speak("I couldn't understand what files to search for.")
            return False

    def handle_password(self, command):
        """Handle password-related commands"""
        if "generate" in command:
            self.generate_password(command)
        elif "check" in command or "strength" in command:
            self.check_password_strength(command)
        else:
            self.speak("Would you like to generate a password or check password strength?")

    def generate_password(self, command):
        """Generate a random password"""
        try:
            # Parse length from command
            length = 12  # Default length
            length_match = re.search(r'(\d+)\s*characters', command)
            if length_match:
                length = int(length_match.group(1))

            # Check if specific requirements are mentioned
            include_uppercase = "uppercase" in command or "capital" in command
            include_lowercase = not ("no lowercase" in command or "without lowercase" in command)
            include_numbers = "numbers" in command or "digits" in command
            include_symbols = "symbols" in command or "special" in command

            # If no specific requirements, include all character types
            if not any([include_uppercase, include_lowercase, include_numbers, include_symbols]):
                include_uppercase = include_lowercase = include_numbers = include_symbols = True

            # Create character sets based on requirements
            chars = ""
            if include_lowercase:
                chars += string.ascii_lowercase
            if include_uppercase:
                chars += string.ascii_uppercase
            if include_numbers:
                chars += string.digits
            if include_symbols:
                chars += string.punctuation

            if not chars:
                self.speak("I need at least one character type to generate a password.")
                return

            # Generate password
            password = ''.join(random.choice(chars) for _ in range(length))

            self.speak(f"I've generated a {length}-character password. The password is: {' '.join(password)}")
            print(f"Generated password: {password}")
        except Exception as e:
            self.speak(f"Sorry, I couldn't generate a password. {str(e)}")

    def check_password_strength(self, command):
        """Check the strength of a password"""
        try:
            # Ask the user to type their password
            self.speak("Please type the password you want to check in the console. It won't be spoken out loud for security.")
            print("Type password here: ", end="")
            password = input()

            if not password:
                self.speak("No password was entered.")
                return

            # Check password strength
            length_score = min(len(password) / 12, 1.0) * 25  # Length up to 12 chars gets 25 points

            has_lower = any(c.islower() for c in password)
            has_upper = any(c.isupper() for c in password)
            has_digit = any(c.isdigit() for c in password)
            has_symbol = any(c in string.punctuation for c in password)

            variety_score = (has_lower + has_upper + has_digit + has_symbol) * 15  # Each type worth 15 points

            # Check for common patterns
            patterns = [
                r'12345', r'qwerty', r'password', r'admin', r'welcome',
                r'123123', r'abcabc', r'\d{4}', r'([a-zA-Z])\1\1'  # Repeated chars
            ]

            pattern_deduction = 0
            for pattern in patterns:
                if re.search(pattern, password.lower()):
                    pattern_deduction += 15

            # Calculate final score
            score = min(length_score + variety_score - pattern_deduction, 100)
            score = max(score, 0)  # Ensure score isn't negative

            # Determine strength category
            if score >= 80:
                strength = "very strong"
            elif score >= 60:
                strength = "strong"
            elif score >= 40:
                strength = "moderate"
            elif score >= 20:
                strength = "weak"
            else:
                strength = "very weak"

            self.speak(f"The password strength is {strength} with a score of {int(score)} out of 100.")
            print(f"Password strength: {strength} ({int(score)}/100)")

            # Provide improvement suggestions
            suggestions = []
            if len(password) < 12:
                suggestions.append("increase the length to at least 12 characters")
            if not has_lower:
                suggestions.append("add lowercase letters")
            if not has_upper:
                suggestions.append("add uppercase letters")
            if not has_digit:
                suggestions.append("add numbers")
            if not has_symbol:
                suggestions.append("add special characters")

            if suggestions:
                suggestion_text = ", ".join(suggestions[:-1])
                if len(suggestions) > 1:
                    suggestion_text += f", and {suggestions[-1]}"
                else:
                    suggestion_text = suggestions[0]
                self.speak(f"To improve your password, you could {suggestion_text}.")
        except Exception as e:
            self.speak(f"Sorry, I couldn't check the password strength. {str(e)}")

    def convert_currency(self, command):
        """Convert currency from one type to another"""
        try:
            # Parse the command to get currencies and amount
            amount_match = re.search(r'(\d+(\.\d+)?)', command)
            from_currency_match = re.search(r'from\s+(\w{3})', command)
            to_currency_match = re.search(r'to\s+(\w{3})', command)
            
            # Currency mapping dictionary
            currency_map = {
                'dollars': 'USD', 'usd': 'USD', 'dollar': 'USD', 'us dollar': 'USD', 'us dollars': 'USD',
                'euros': 'EUR', 'euro': 'EUR', 'eur': 'EUR',
                'pounds': 'GBP', 'pound': 'GBP', 'gbp': 'GBP', 'british pound': 'GBP',
                'yen': 'JPY', 'jpy': 'JPY', 'japanese yen': 'JPY',
                'yuan': 'CNY', 'cny': 'CNY', 'chinese yuan': 'CNY',
                'rupees': 'INR', 'rupee': 'INR', 'inr': 'INR', 'indian rupee': 'INR'
            }
            
            # Extract currencies from text
            if not from_currency_match or not to_currency_match:
                for currency_name, code in currency_map.items():
                    if currency_name in command.lower():
                        pos = command.lower().find(currency_name)
                        if 'to' in command.lower()[pos:]:
                            if not from_currency_match:
                                from_currency_match = type('obj', (), {'group': lambda x: code})
                        else:
                            if not to_currency_match:
                                to_currency_match = type('obj', (), {'group': lambda x: code})
            
            # Interactive mode if information is missing
            amount = float(amount_match.group(1)) if amount_match else None
            from_currency = from_currency_match.group(1).upper() if from_currency_match else None
            to_currency = to_currency_match.group(1).upper() if to_currency_match else None
            
            if amount is None:
                self.speak("What amount would you like to convert?")
                amount = float(input("Enter amount: "))
            
            if from_currency is None:
                self.speak("What currency are you converting from? Please enter the 3-letter currency code.")
                from_currency = input("From currency (e.g., USD): ").upper()
            
            if to_currency is None:
                self.speak("What currency are you converting to? Please enter the 3-letter currency code.")
                to_currency = input("To currency (e.g., EUR): ").upper()
            
            # Use ExchangeRate-API (free tier) instead of forex-python
            api_url = f"https://open.er-api.com/v6/latest/{from_currency}"
            
            try:
                response = requests.get(api_url)
                data = response.json()
                
                if data["result"] == "success":
                    rates = data["rates"]
                    if to_currency in rates:
                        conversion_rate = rates[to_currency]
                        converted_amount = amount * conversion_rate
                        
                        # Format the output
                        self.speak(f"{amount} {from_currency} is equal to {converted_amount:.2f} {to_currency}.")
                        self.speak(f"The current exchange rate is 1 {from_currency} = {conversion_rate:.4f} {to_currency}.")
                        print(f"{amount} {from_currency} = {converted_amount:.2f} {to_currency}")
                        print(f"Rate: 1 {from_currency} = {conversion_rate:.4f} {to_currency}")
                    else:
                        self.speak(f"Sorry, I couldn't find the conversion rate for {to_currency}.")
                else:
                    self.speak("I couldn't retrieve the current exchange rates.")
            except Exception as e:
                self.speak(f"I couldn't perform that conversion. Please check your internet connection and try again.")
                print(f"Conversion error: {str(e)}")
        except Exception as e:
            self.speak(f"Sorry, I encountered an error while converting currency: {str(e)}")

    def generate_code(self, command: str) -> None:
        """Generate code using Gemini API based on user's description"""
        try:
            if not self.gemini_model:
                self.speak("Sorry, the Gemini API is not configured properly.")
                return

            # Extract the programming task from the command
            # Remove trigger phrases to get the actual request
            code_request = command
            for trigger in ["generate code", "write code", "code for", "implement"]:
                code_request = code_request.replace(trigger, "").strip()

            if not code_request or code_request.lower() in ["for", "to", "that"]:
                self.speak("What code would you like me to generate? Please describe the functionality.")
                with sr.Microphone() as source:
                    self.speak("I'm listening...")
                    audio = self.recognizer.listen(source)
                    try:
                        code_request = self.recognizer.recognize_google(audio)
                        print(f"You requested: {code_request}")
                    except:
                        self.speak("Sorry, I couldn't understand your request.")
                        return

            # Enhance the prompt for better code generation
            enhanced_prompt = f"""
            Generate clean, well-commented, production-quality code for the following task:

            {code_request}

            Include:
            - Appropriate imports
            - Clear comments explaining the logic
            - Error handling where appropriate
            - Example usage if possible

            Return ONLY the code without additional explanations.
            """

            self.speak(f"Generating code for: {code_request}")
            print(f"Generating code using Gemini API...")

            # Generate code using Gemini
            response = self.gemini_model.generate_content(enhanced_prompt)

            if not response or not response.text:
                self.speak("I couldn't generate code for that request.")
                return

            # Extract code from response
            code = response.text.strip()

            # Clean up the code (remove markdown code blocks if present)
            if "```" in code:
                code_blocks = code.split("```")
                for block in code_blocks:
                    if block.strip() and not block.strip().startswith(('python', 'java', 'c++', 'c#', 'javascript')):
                        code = block.strip()
                        break

            # Check if the extracted code is still empty
            if not code.strip():
                self.speak("I couldn't extract a valid code block.")
                return

                    
            # Print the generated code
            print("\n----- GENERATED CODE -----\n")
            print(code)
            print("\n--------------------------\n")

            # Speak a summary
            self.speak("I've generated the code for your request. You can see it in the console.")
            self.speak("Would you like me to explain this code or save it to a file?")

            # Listen for user's response about explaining or saving
            with sr.Microphone() as source:
                audio = self.recognizer.listen(source)
                try:
                    response = self.recognizer.recognize_google(audio).lower()
                    print(f"You said: {response}")

                    if "explain" in response:
                        explanation_prompt = f"Explain the following code in simple terms:\n\n{code}"
                        explanation = self.gemini_model.generate_content(explanation_prompt).text
                        self.speak("Here's an explanation of the code:")
                        print("\n----- CODE EXPLANATION -----\n")
                        print(explanation)
                        print("\n----------------------------\n")
                        self.speak(explanation)

                    elif "save" in response or "file" in response:
                        # Determine filename and language
                        language_extensions = {
                            "python": ".py", "java": ".java", "javascript": ".js", "html": ".html",
                            "css": ".css", "c++": ".cpp", "c#": ".cs", "go": ".go", "ruby": ".rb",
                            "php": ".php", "rust": ".rs", "swift": ".swift", "typescript": ".ts"
                        }

                        # Try to determine language from the code or prompt
                        extension = ".txt"  # Default
                        for lang, ext in language_extensions.items():
                            if lang in code_request.lower() or lang in code.lower():
                                extension = ext
                                break

                        # Create a timestamped filename
                        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                        filename = f"generated_code_{timestamp}{extension}"

                        # Save the code to a file
                        with open(filename, "w") as f:
                            f.write(code)

                        self.speak(f"Code has been saved to {filename}")

                except:
                    self.speak("I didn't catch your response. The code is available in the console output.")

        except Exception as e:
            self.speak(f"Sorry, I encountered an error while generating code: {str(e)}")
            print(f"Code generation error: {str(e)}")

if __name__ == "__main__":
    assistant = VoiceAssistant("Neura") 
    assistant.run()