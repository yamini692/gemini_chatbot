import requests

def get_weather(city):
    api_key = "c6b2169f47dae501f671bf1773a89b4b"  # Your OpenWeatherMap key
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"

    try:
        response = requests.get(url)
        data = response.json()

        if response.status_code != 200 or "main" not in data:
            print(f"[❌] Error: {data.get('message', 'Unknown error')}")
            return

        temp = data["main"]["temp"]
        description = data["weather"][0]["description"]
        print(f"[✅] {city}: {temp}°C, {description}")
    
    except Exception as e:
        print(f"[❌] Exception: {e}")

# 🔍 Test it
get_weather("Chennai")
