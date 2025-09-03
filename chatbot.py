import os
from typing import List
from io import BytesIO # <- Tambahkan import ini
from datetime import datetime #

from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from telegram import Update

from agno.agent import Agent
from agno.models.google import Gemini

# --- Konfigurasi ---
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# --- Agent untuk Chat Teks Biasa ---
text_agent = Agent(
    model=Gemini(id="gemini-2.5-pro"), # <-- Ganti ID model di sini
    markdown=True,
    add_datetime_to_instructions=True,
    instructions=[
        "Be concise and helpful.",
        "Use tables for structured data when appropriate.",
    ],
)

# --- Agent Khusus untuk Generate Gambar ---
# Model ini secara spesifik dioptimalkan untuk membuat gambar.
image_agent = Agent(
    model=Gemini(
        # Kita coba model eksperimental yang juga tersedia untuk Anda
        id="gemini-2.0-flash-preview-image-generation", 
        response_modalities=["Text", "Image"],
    ),
    debug_mode=True 
)


# --- Handler untuk Perintah /start ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Mengirim pesan sambutan saat perintah /start dipanggil."""
    welcome_text = (
        "Halo! Saya adalah bot Gemini. ✨\n\n"
        "Anda bisa langsung mengobrol dengan saya.\n\n"
        "Untuk membuat gambar, gunakan perintah:\n"
        "`/generate deskripsi_gambar_anda`\n\n"
        "Contoh: `/generate seekor kucing oranye di luar angkasa`"
    )
    await update.message.reply_text(welcome_text, parse_mode='Markdown')


# --- Handler untuk Pesan Teks (Ngobrol Biasa) ---
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Menangani pesan teks biasa dan membalas menggunakan text_agent."""
    text = update.message.text or ""
    
    # Menampilkan notifikasi "sedang mengetik..."
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action='typing')
    
    chunks: List[str] = []
    for ev in text_agent.run(text, stream=True):
        if getattr(ev, "content", None):
            chunks.append(ev.content)
            
    reply = "".join(chunks).strip() or "Maaf, saya tidak bisa merespons saat ini."
    await update.message.reply_text(reply, disable_web_page_preview=True)


# --- Handler BARU untuk Perintah /generate ---
async def generate_image(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Membuat gambar, menyimpannya secara lokal, dan mengirimkannya ke Telegram."""
    prompt = " ".join(context.args)

    if not prompt:
        await update.message.reply_text(
            "Tolong berikan deskripsi gambar setelah perintah.\n"
            "Contoh: `/generate seekor naga sedang minum kopi`"
        )
        return

    processing_message = await update.message.reply_text(f"🎨 Sedang membuat gambar untuk: \"{prompt}\"...")

    try:
        response = image_agent.run(prompt)
        image_bytes = getattr(response, 'image', None)
        
        await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=processing_message.message_id)

        # HANYA JIKA GAMBAR BERHASIL DIBUAT (image_bytes tidak kosong)
        if image_bytes:
            # --- BLOK KODE BARU UNTUK MENYIMPAN FILE ---
            # 1. Tentukan nama folder
            output_folder = "generated_images"
            
            # 2. Buat folder jika belum ada
            os.makedirs(output_folder, exist_ok=True)
            
            # 3. Buat nama file yang unik berdasarkan waktu
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{timestamp}_{prompt[:20].replace(' ', '_')}.png"
            filepath = os.path.join(output_folder, filename)
            
            # 4. Tulis data bytes ke dalam file
            with open(filepath, "wb") as f:
                f.write(image_bytes)
            
            print(f"✅ Gambar berhasil disimpan di: {filepath}")
            # --- AKHIR BLOK KODE BARU ---

            # Kirim foto ke Telegram (kode ini tetap sama)
            final_caption = getattr(response, 'content', None) or prompt
            await update.message.reply_photo(
                photo=BytesIO(image_bytes),
                caption=final_caption
            )
        else:
            # JIKA GAMBAR GAGAL DIBUAT (outputnya teks)
            error_content = getattr(response, 'content', "gagal membuat gambar. Coba deskripsi yang lain.")
            await update.message.reply_text(f"Maaf, {error_content}")
            print(f"⚠️ Pembuatan gambar gagal. Respons teks dari AI: {error_content}")
            
    except Exception as e:
        print(f"Error saat generate gambar: {e}")
        await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=processing_message.message_id)
        await update.message.reply_text("Terjadi kesalahan teknis saat mencoba membuat gambar.")


# --- Fungsi Utama untuk Menjalankan Bot ---
def main() -> None:
    """Fungsi utama untuk menjalankan bot Telegram."""
    if not TELEGRAM_BOT_TOKEN:
        raise RuntimeError(
            "TELEGRAM_BOT_TOKEN belum disetel. Set di environment terlebih dahulu."
        )

    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Daftarkan semua handler
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("generate", generate_image)) # <- Daftarkan handler baru
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    print("Bot sedang berjalan...")
    app.run_polling()


if __name__ == "__main__":
    main()