from agno.agent import Agent
from agno.app.whatsapp.app import WhatsappAPI
from agno.models.google import Gemini
from dotenv import load_dotenv
import os
from collections import defaultdict

# --- Load environment variables ---
load_dotenv()

# --- DEBUG: cek .env ---
print("========================")
print("MEMERIKSA VARIABEL .ENV:")
print(f"VERIFY_TOKEN:   '{os.getenv('WHATSAPP_VERIFY_TOKEN')}'")
print(f"PHONE_ID:       '{os.getenv('WHATSAPP_PHONE_NUMBER_ID')}'")
print(f"ACCESS_TOKEN:   '{os.getenv('WHATSAPP_ACCESS_TOKEN')}'")
print(f"GOOGLE_API_KEY: '{os.getenv('GOOGLE_API_KEY')}'")
print("========================")

# --- AGENT GAMBAR (text + image) ---
image_agent = Agent(
    model=Gemini(
        id="gemini-2.0-flash-exp-image-generation",
        response_modalities=["Text", "Image"],
    ),
    debug_mode=True,
)

# --- MEMORI PER USER ---
user_memory = defaultdict(lambda: {"history": [], "images": []})
# Struktur:
# {
#   user_id: {
#       "history": ["User: ..", "Bot: .."],
#       "images": ["url1", "url2", ...]
#   }
# }

# --- CUSTOM WHATSAPP API ---
class MemoryWhatsappAPI(WhatsappAPI):
    async def handle_message(self, message, agent=None):
        user_id = message["from"]

        # --- CEK JIKA ADA GAMBAR ---
        if "image" in message:
            image_id = message["image"]["id"]
            image_url = await self.download_media(image_id)  # ambil url media WA
            user_memory[user_id]["images"].append(image_url)

            await self.send_message(
                to=user_id,
                text=f"Gambar diterima! (total {len(user_memory[user_id]['images'])} gambar tersimpan)"
            )
            return

        # --- CEK INPUT TEXT ---
        text = message.get("text", {}).get("body", "")

        # Jika user minta gabungkan gambar
        if "gabungkan gambar" in text.lower():
            if len(user_memory[user_id]["images"]) < 2:
                await self.send_message(
                    to=user_id,
                    text="Kirim minimal 2 gambar dulu sebelum bisa digabungkan 👍"
                )
                return

            # Ambil 2 gambar terakhir
            img1, img2 = user_memory[user_id]["images"][-2:]

            # Prompt untuk gabungkan
            # Prompt + 2 gambar dikirim ke model
            prompt = "Gabungkan kedua gambar ini menjadi satu gambar komposit yang menarik. Pastikan objek dari kedua gambar terlihat jelas dan proporsional."

            response = await self.agent.run(
                prompt,
                images=[img1, img2]  # ✅ kirim 2 gambar ke Gemini
            )



            if hasattr(response, "images") and response.images:
                await self.send_message(
                    to=user_id,
                    image=response.images[0],
                    text="Ini hasil gabungan 2 gambarmu 🎨"
                )
            else:
                await self.send_message(
                    to=user_id,
                    text="Maaf, gagal menggabungkan gambar 😢"
                )
            return

        # --- JALANKAN AGENT UNTUK TEXT BIASA ---
        history = user_memory[user_id]["history"][-5:]
        combined_prompt = "\n".join(history + [text])

        response = await self.agent.run(combined_prompt)

        # Simpan riwayat
        user_memory[user_id]["history"].append(f"User: {text}")
        user_memory[user_id]["history"].append(f"Bot: {response.text or '[gambar]'}")

        # Kirim respon
        if hasattr(response, "images") and response.images:
            await self.send_message(
                to=user_id,
                image=response.images[0],
                text=response.text or "Ini hasil gambarnya 😊"
            )
        else:
            await self.send_message(
                to=user_id,
                text=response.text or "Maaf, tidak ada jawaban."
            )


# --- WHATSAPP APP ---
whatsapp_app = MemoryWhatsappAPI(
    agent=image_agent,
    name="Image + Memory Bot",
    app_id="image_generation_model",
    description="Bot yang bisa generate/edit gambar, simpan riwayat, dan gabungkan 2 gambar."
)

# --- ASGI APP ---
app = whatsapp_app.get_app()

# --- RUN SERVER ---
if __name__ == "__main__":
    whatsapp_app.serve(app=app, port=8000)
