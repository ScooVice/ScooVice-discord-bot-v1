import discord
from discord.ext import commands
from groq import Groq
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Konfigurasi
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
GROQ_API_KEY = os.getenv('GROQ_API_KEY')

# Setup Groq
client = Groq(api_key=GROQ_API_KEY)

# Setup Discord Bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Dictionary untuk menyimpan conversation history per user
conversation_history = {}

@bot.event
async def on_ready():
    print(f'{bot.user} sudah online dan siap digunakan!')
    print(f'Bot ID: {bot.user.id}')
    print('------')

@bot.event
async def on_message(message):
    # Jangan respon pesan dari bot sendiri
    if message.author == bot.user:
        return
    
    # Process commands terlebih dahulu
    await bot.process_commands(message)
    
    # Cek apakah bot di-mention atau ini DM
    if bot.user.mentioned_in(message) or isinstance(message.channel, discord.DMChannel):
        # Hapus mention dari pesan
        content = message.content.replace(f'<@{bot.user.id}>', '').strip()
        
        if not content:
            await message.channel.send("Halo! Ada yang bisa saya bantu? 😊")
            return
        
        # Tampilkan typing indicator
        async with message.channel.typing():
            try:
                # Ambil atau buat conversation history untuk user ini
                user_id = str(message.author.id)
                if user_id not in conversation_history:
                    conversation_history[user_id] = [
                        {"role": "system", "content": "Kamu adalah AI assistant yang helpful dan ramah. Jawab dalam bahasa Indonesia kecuali diminta bahasa lain."}
                    ]
                
                # Tambahkan pesan user ke history
                conversation_history[user_id].append({
                    "role": "user",
                    "content": content
                })
                
                # Batasi history maksimal 10 pesan terakhir (untuk hemat token)
                if len(conversation_history[user_id]) > 21:  # 1 system + 20 messages
                    conversation_history[user_id] = [conversation_history[user_id][0]] + conversation_history[user_id][-20:]
                
                # Panggil Groq API
                chat_completion = client.chat.completions.create(
                    messages=conversation_history[user_id],
                    model="llama-3.3-70b-versatile",  # Model terbaik & tercepat dari Groq
                    temperature=0.7,
                    max_tokens=1024,
                )
                
                # Ambil response dari AI
                ai_response = chat_completion.choices[0].message.content
                
                # Simpan response AI ke history
                conversation_history[user_id].append({
                    "role": "assistant",
                    "content": ai_response
                })
                
                # Split pesan jika terlalu panjang (Discord limit 2000 karakter)
                if len(ai_response) > 2000:
                    chunks = [ai_response[i:i+2000] for i in range(0, len(ai_response), 2000)]
                    for chunk in chunks:
                        await message.channel.send(chunk)
                else:
                    await message.channel.send(ai_response)
                    
            except Exception as e:
                error_message = f"Maaf, terjadi error: {str(e)}"
                await message.channel.send(error_message)
                print(f"Error: {e}")

@bot.command(name='reset')
async def reset_conversation(ctx):
    """Reset conversation history untuk user"""
    user_id = str(ctx.author.id)
    if user_id in conversation_history:
        del conversation_history[user_id]
    await ctx.send("✅ Conversation history sudah di-reset!")

@bot.command(name='bothelp')
async def help_command(ctx):
    """Tampilkan panduan penggunaan bot"""
    help_text = """
    **🤖 Panduan Bot AI (Powered by Groq)**
    
    **Cara menggunakan:**
    • Mention bot (@BotName) diikuti pesanmu
    • Atau kirim DM langsung ke bot
    
    **Commands:**
    • `!reset` - Reset conversation history
    • `!bothelp` - Tampilkan panduan ini
    
    **Contoh:**
    `@BotName apa itu Python?`
    `@BotName buatin saya joke lucu`
    
    **Model:** Llama 3.3 70B (Groq - Gratis & Super Cepat!)
    """
    await ctx.send(help_text)

@bot.command(name='model')
async def show_model(ctx):
    """Tampilkan info model yang digunakan"""
    info = """
    **🚀 Model Info:**
    • **Provider:** Groq (FREE!)
    • **Model:** Llama 3.3 70B Versatile
    • **Speed:** Ultra Fast ⚡
    • **Cost:** $0.00 (Gratis Unlimited!)
    """
    await ctx.send(info)

# Test baca environment variables
print("=== DEBUG INFO ===")
print(f"DISCORD_TOKEN loaded: {DISCORD_TOKEN is not None and DISCORD_TOKEN != ''}")
print(f"GROQ_API_KEY loaded: {GROQ_API_KEY is not None and GROQ_API_KEY != ''}")
print(f"Token length: {len(DISCORD_TOKEN) if DISCORD_TOKEN else 0}")
print(f"API Key length: {len(GROQ_API_KEY) if GROQ_API_KEY else 0}")
print("==================")

# Jalankan bot
if __name__ == "__main__":
    if not DISCORD_TOKEN or not GROQ_API_KEY:
        print("ERROR: Token Discord atau Groq API Key tidak ditemukan!")
        print("Pastikan file .env sudah dibuat dengan benar.")
    else:
        bot.run(DISCORD_TOKEN)