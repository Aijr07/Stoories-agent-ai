import os
from dotenv import load_dotenv
load_dotenv()

from agno.agent import Agent
from agno.app.whatsapp.app import WhatsappAPI
from agno.models.google import Gemini

# ==============================================================================
# AGEN 1: KHUSUS UNTTUK PERCAKAPAN TEKS
# ==============================================================================
text_agent = Agent(
    model=Gemini(
        id="gemini-1.5-flash",
        response_modalities=["Text"],
    ),
    instructions="You are a friendly and helpful WhatsApp assistant. Answer the user's questions clearly and concisely in Indonesian.",
    debug_mode=True,
)

# ==============================================================================
# AGEN 2: KHUSUS UNTUK MEMBUAT GAMBAR
# ==============================================================================
image_agent = Agent(
    model=Gemini(
        id="gemini-1.5-flash",
        response_modalities=["Image", "Text"],
    ),
    instructions="You are an image generation AI. The user will provide a prompt, and you must generate an image based on that prompt. Only generate images.",
    debug_mode=True,
)

# ==============================================================================
# ROUTER: Logika untuk memilih agen mana yang akan digunakan
# ==============================================================================
class RouterAgent(Agent):
    def __init__(self, text_agent: Agent, image_agent: Agent):
        # <<< PERBAIKAN DI SINI
        # Panggil constructor dari parent class (Agent) untuk inisialisasi internal
        # Kita bisa gunakan salah satu model agen sebagai dasar
        super().__init__(model=text_agent.model, debug_mode=True)
        # >>> AKHIR PERBAIKAN

        self.text_agent = text_agent
        self.image_agent = image_agent
        self.image_keywords = ["buatkan gambar", "generate image", "gambar", "lukis", "create image"]

    def process(self, message, **kwargs):
        user_input = ""
        if message and "text" in message and "body" in message["text"]:
            user_input = message["text"]["body"].lower()

        if any(keyword in user_input for keyword in self.image_keywords):
            print("DEBUG: Routing to Image Agent")
            return self.image_agent.process(message, **kwargs)
        else:
            print("DEBUG: Routing to Text Agent")
            return self.text_agent.process(message, **kwargs)

master_agent = RouterAgent(text_agent=text_agent, image_agent=image_agent)

# ==============================================================================
# KONFIGURASI APLIKASI WHATSAPP
# ==============================================================================
whatsapp_app = WhatsappAPI(
    agent=master_agent,
    name="Advanced AI Assistant",
    app_id="advanced_ai_assistant",
    description="An advanced model that routes tasks to specialized agents.",
)

app = whatsapp_app.get_app()

if __name__ == "__main__":
    whatsapp_app.serve(app="image_generation_model:app", port=8000, reload=True)