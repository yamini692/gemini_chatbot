import os
import re
import requests
import gradio as gr
from datetime import datetime
from typing import Literal
from dotenv import load_dotenv, find_dotenv
import random

# Load and set API keys
load_dotenv(find_dotenv())
os.environ["GOOGLE_API_KEY"] = os.getenv("GEMINI_API_KEY")
os.environ["WEATHER_API_KEY"] = os.getenv("WEATHER_API_KEY")

# Configure Gemini
import google.generativeai as genai
genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
model = genai.GenerativeModel("gemini-2.5-flash")

# LangChain setup
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import Tool, initialize_agent
from langchain.agents.agent_types import AgentType

llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.5)


def get_weather(location: str, unit: Literal["celsius", "fahrenheit"] = "celsius"):
    base_url = "http://api.weatherapi.com/v1/current.json"
    api_key = os.environ["WEATHER_API_KEY"]

    params = {
        "key": api_key,
        "q": location,
        "aqi": "no"
    }

    try:
        response = requests.get(base_url, params=params, timeout=5)
        data = response.json()

        if "error" in data:
            return {"error": data["error"]["message"]}

        current = data["current"]
        location_name = data["location"]["name"]

        temp = current["temp_c"] if unit == "celsius" else current["temp_f"]
        return {
            "city": location_name,
            "temperature": temp,
            "humidity": current["humidity"],
            "condition": current["condition"]["text"],
            "wind_speed": current["wind_kph"],
            "unit": unit,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        return {"error": str(e)}

# Wrap weather response
def weather_tool_wrapper(city: str) -> str:
    data = get_weather(city)
    if "error" in data:
        return f"Error: {data['error']}"
    dt = datetime.now().strftime("%B %d, %Y at %I:%M %p")

    responses = [
    f"As of {dt}, in {data['city']} the weather is {data['condition']}. The temperature is about {data['temperature']}°{'C' if data['unit']=='celsius' else 'F'}, with humidity at {data['humidity']}% and wind speed reaching {data['wind_speed']} kph. Stay prepared.",

    f"Right now in {data['city']} ({dt}), it feels like {data['condition']}. Temperature is {data['temperature']}°{data['unit'][0].upper()}, wind blowing at {data['wind_speed']} kph, and humidity stands at {data['humidity']}%. Plan your outdoor activities accordingly and stay weather-aware.",

    f"Here's your {dt} weather report for {data['city']}: Expect {data['condition']} with a temperature of {data['temperature']}°{data['unit'][0].upper()}, wind speeds around {data['wind_speed']} kph, and {data['humidity']}% humidity. Dress accordingly and stay hydrated throughout the day."
]


    return random.choice(responses)

# Register tool & agent
weather_tool = Tool(
    name="WeatherTool",
    func=weather_tool_wrapper,
    description="Get current weather by city name."
)

agent = initialize_agent(
    tools=[weather_tool],
    llm=llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    handle_parsing_errors=True,
    verbose=False
)

# Extract city name using Gemini
def extract_location(query: str) -> str:
    prompt = f"Extract the city name from: {query}"
    try:
        txt = model.generate_content(prompt).text.strip().strip(".")
        return re.sub(r"\(.*?\)", "", txt).strip()
    except:
        return query

# Smart reply using LangChain + Gemini
def smart_reply_gradio(query, chat_history):
    chat_history.append((query, "Thinking..."))
    yield "", chat_history

    lower = query.lower()
    weather_keywords = ['weather', 'forecast', 'climate', 'temperature', 'humidity', 'wind']

    try:
        if any(w in lower for w in weather_keywords):
            city = extract_location(query)
            response = agent.run(f"What is the weather in {city}?")
        else:
            response = model.generate_content(query).text.strip()
    except Exception as e:
        response = f"Error: {str(e)}"

    chat_history[-1] = (query, response)
    yield "", chat_history


with gr.Blocks() as demo:
    gr.Markdown("Gemini Weather Assistant")
    chatbot = gr.Chatbot(label="YazBot")
    user_msg = gr.Textbox(placeholder="Ask about weather or anything...")
    gr.ClearButton([chatbot, user_msg])
    user_msg.submit(
        smart_reply_gradio,
        inputs=[user_msg, chatbot],
        outputs=[user_msg, chatbot],
        queue=True
    )

# Launch
demo.launch()
