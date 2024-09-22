# This file is for a simple text to speech 

import pyttsx3

# Initialize the TTS engine
engine = pyttsx3.init()

# Text you want to convert to speech
text = "Hello"

# Convert text to speech
engine.say(text)

# Set Rate
engine.setProperty('rate', 150)  # Speed of speech

# Set Volume
engine.setProperty('volume', 0.8)  # Volume level between 0 and 1

# Choose Voice
voices = engine.getProperty('voices')
engine.setProperty('voice', voices[1].id)  # 0 for male, 1 for female

# Play the speech
engine.runAndWait()

engine = pyttsx3.init()

# Get user input
text = input("Enter the text you want to convert to speech: ")

engine.say(text)
engine.runAndWait()