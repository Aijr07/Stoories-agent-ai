import os
import google.generativeai as genai

# Pastikan Anda sudah mengatur GOOGLE_API_KEY di environment Anda
# Jika belum, hapus tanda # di bawah dan masukkan kunci API Anda di sini
# os.environ['GOOGLE_API_KEY'] = "MASUKKAN_KUNCI_API_ANDA_DI_SINI"

try:
    # Mengambil kunci API dari environment variable
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY environment variable not set.")
    
    genai.configure(api_key=api_key)

    print("✅ Berhasil terhubung ke Google AI. Mencari model yang tersedia...")
    print("-" * 50)
    print("Model yang mendukung 'generateContent' (cocok untuk bot):")
    
    found_model = False
    for model in genai.list_models():
        # Kita hanya tertarik pada model yang mendukung metode 'generateContent'
        if 'generateContent' in model.supported_generation_methods:
            print(f"-> {model.name}")
            found_model = True
            
    if not found_model:
        print("\n⚠️ Tidak ada model yang mendukung 'generateContent' ditemukan.")

    print("-" * 50)

except Exception as e:
    print(f"❌ Terjadi kesalahan: {e}")
    print("Pastikan GOOGLE_API_KEY Anda sudah benar dan di-set sebagai environment variable.")