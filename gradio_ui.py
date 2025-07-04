import os
import re
import json
import requests
import gradio as gr
import google.generativeai as genai
from dotenv import load_dotenv, find_dotenv
from datetime import datetime
from typing import List, Literal

# --- Load & Configure ---
load_dotenv(find_dotenv())
GOOGLE_API_KEY = os.getenv("GEMINI_API_KEY")
WEATHER_API_KEY = "e9283ae8b8a9a837c00c30344d383ed6"

genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

# --- Weather Logic ---
def get_weather(location: str, unit: Literal["celsius", "fahrenheit"] = "celsius"):
    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": location,
        "appid": WEATHER_API_KEY,
        "units": "metric" if unit == "celsius" else "imperial"
    }

    try:
        response = requests.get(url, params=params, timeout=5)
        data = response.json()

        if response.status_code != 200:
            return {"error": data.get("message", "Unknown error")}

        return {
            "city": data["name"],
            "temperature": data["main"]["temp"],
            "humidity": data["main"]["humidity"],
            "condition": data["weather"][0]["description"],
            "wind_speed": data["wind"]["speed"],
            "unit": unit,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        return {"error": str(e)}

def extract_location(query: str) -> str:
    location_prompt = f"Extract the city or country name only from this query: {query}. Just return the city name."
    try:
        loc_response = model.generate_content(location_prompt)
        raw = loc_response.text.strip().strip(".")
        return re.sub(r"\(.*?\)", "", raw).strip()
    except:
        return "your location"

def process_weather_query(query: str) -> str:
    location = extract_location(query)
    unit = "fahrenheit" if "fahrenheit" in query.lower() else "celsius"

    weather = get_weather(location, unit)

    if "error" in weather:
        return f"Could not fetch weather for {location}. Reason: {weather['error']}"

    summary_prompt = f"""
User query: '{query}'

Weather data:
{json.dumps(weather, indent=2)}

Write a user-friendly weather report in **exactly 50 words**. 
Include city name, temperature (in {unit}), condition, humidity, and wind speed.
Avoid repeating values. Do not add emojis. Be helpful and natural.
"""

    try:
        reply = model.generate_content(summary_prompt)
        return reply.text.strip()
    except Exception as e:
        return f"Error generating reply: {str(e)}"

# --- Gradio Chat Logic ---
def handle_user_query(msg, chatbot):
    chatbot = chatbot + [[msg, None]]
    return '', chatbot

def generate_chatbot(chatbot: List[List[str]]) -> List[dict]:
    formatted = []
    for ch in chatbot:
        if ch[0]: formatted.append({"role": "user", "parts": [ch[0]]})
        if ch[1]: formatted.append({"role": "model", "parts": [ch[1]]})
    return formatted

def handle_gemini_response(chatbot):
    query = chatbot[-1][0]
    formatted_chatbot = generate_chatbot(chatbot[:-1])

    weather_keywords = ['weather', 'temperature', 'forecast', 'humidity', 'wind', 'climate']
    if any(word in query.lower() for word in weather_keywords):
        answer = process_weather_query(query)
    else:
        chat = model.start_chat(history=formatted_chatbot)
        response = chat.send_message(query)
        answer = response.text.strip()

    chatbot[-1][1] = answer
    return chatbot

# --- Gradio UI ---
with gr.Blocks() as demo:
    gr.Markdown("## 🌤️ Gemini Chat + 50-word Weather Summary Bot")
    chatbot = gr.Chatbot(label="Chat History", bubble_full_width=False)
    msg = gr.Textbox(placeholder="Ask about weather or anything...")

    clear = gr.ClearButton([msg, chatbot])

    msg.submit(
        handle_user_query,
        inputs=[msg, chatbot],
        outputs=[msg, chatbot]
    ).then(
        handle_gemini_response,
        inputs=[chatbot],
        outputs=[chatbot]
    )

if __name__ == "__main__":
    demo.queue()
    demo.launch()
