import gradio as gr
from fastapi import FastAPI
from gradio_ui import demo

from gradio.routes import mount_gradio_app

app = FastAPI()

@app.get("/")
def home():
    return {"message": "Gradio UI is running at /gradio"}

app = mount_gradio_app(app, demo, path="/gradio")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
