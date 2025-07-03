import os
import gradio as gr
import google.generativeai as genai
from dotenv import load_dotenv, find_dotenv
from langchain_community.tools.tavily_search.tool import TavilySearchResults

# === Load environment variables ===
load_dotenv(find_dotenv())
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# === Setup Gemini ===
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("models/gemini-1.5-flash")

# === Setup Tavily tool ===
tavily = TavilySearchResults(tavily_api_key=TAVILY_API_KEY)

# === Response logic ===
def respond(query, history):
    # Decide when to use Tavily
    if "weather" in query.lower() or "search" in query.lower():
        try:
            result = tavily.invoke({"query": query})
            # Format Tavily result into a readable string
            if isinstance(result, dict):
                result = f"{result.get('title', '')} (score: {result.get('score', '')})"
            elif isinstance(result, list):
                result = "\n".join([str(item) for item in result])
            else:
                result = str(result)
            return history + [(query, result)]
        except Exception as e:
            return history + [(query, f"[Tavily Error] {str(e)}")]
    else:
        try:
            response = model.generate_content(query)
            return history + [(query, response.text)]
        except Exception as e:
            return history + [(query, f"[Gemini Error] {str(e)}")]

# === Gradio UI ===
with gr.Blocks() as demo:
    chatbot = gr.Chatbot(label="Gemini + Tavily Agent")
    msg = gr.Textbox(placeholder="Ask anything... like 'What's the weather in Chennai?'", label="Your Message")
    clear = gr.ClearButton([msg, chatbot])

    msg.submit(
        fn=respond,
        inputs=[msg, chatbot],
        outputs=[chatbot]
    )

# === Run app ===
if __name__ == "__main__":
    demo.queue()
    demo.launch(share=True)
