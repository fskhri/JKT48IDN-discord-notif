import discord
from discord.ext import commands, tasks
import requests
import time
from datetime import datetime
import datetime
import pytz
import random

# Inisialisasi bot
bot = commands.Bot(command_prefix='!')

# Nama channel yang akan digunakan untuk notifikasi
channel_name = 'idn'

# Fungsi untuk mengambil data dari API baru
def get_livestream_data():
    api_url = 'https://idn-api-live-jkt48.vercel.app/api/jkt48'
    response = requests.get(api_url)
    data = response.json()

    # Check if the response is a list
    if isinstance(data, list):
        # Assuming the data is a list of livestreams
        livestreams = data
    else:
        # Assuming the data is a dictionary with a 'data' key
        livestreams = data.get('data', [])

    return {'data': livestreams}

# Dictionary untuk menyimpan pesan yang terakhir di-edit untuk setiap live stream
last_messages = {}

# Fungsi yang dijalankan saat bot siap
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="JKT48 Livestreams"))

    # Mulai tugas livestream_notification setiap 5 menit
    livestream_notification.start()

# Fungsi untuk mengirimkan notifikasi atau memperbarui secara berkala
@tasks.loop(minutes=5)
async def livestream_notification():
    livestream_data = get_livestream_data()

    if livestream_data and 'data' in livestream_data and len(livestream_data['data']) > 0:
        for livestream in livestream_data['data']:
            await send_livestream_notification(livestream)

# Fungsi untuk mengirim notifikasi ke semua server
async def send_livestream_notification(livestream):
    print(f"Sending notification for {livestream['title']}")
    random_color = discord.Color(random.randint(0, 0xFFFFFF))  # Random Color For Embed

    # Proses data sesuai kebutuhan
    title = livestream.get('title', 'No Title')
    playback_url = livestream.get('stream_url', '')
    thumbnail_url = livestream.get('image', '')  # Ganti dengan field yang sesuai, bisa 'image' atau 'thumbnail_url'
    view_count = livestream.get('view_count', 0)
    creator_name = livestream.get('user', {}).get('name', 'Unknown')
    username = livestream.get('user', {}).get('username', 'Unknown')
    live_at = livestream.get('live_at', '')
    greeting = get_greeting(live_at)  # Menentukan salam berdasarkan waktu

    # Buat objek embed
    embed = discord.Embed(
        title=title,
        description=f"{greeting}, si {creator_name} lagi live nih! Nonton yuk! 🎥\n"
                    f"**Pemirsa 👥:** {view_count}\n"
                    f"**Pembuat:** {creator_name}",
        color=random_color
    )

    embed.set_thumbnail(url=thumbnail_url)  # Set thumbnail menggunakan URL

    # Tambahkan tombol untuk membuka playback dalam web player
    embed.add_field(name="Web Player", value=f"[Buka di Web Player]({playback_url})", inline=False)

    # Tambahkan tombol untuk membuka channel
    channel_url = f"https://www.idn.app/{username.lower().replace(' ', '')}/live/{livestream.get('slug', '')}"
    embed.add_field(name="Channel", value=f"[Buka Channel]({channel_url})", inline=True)

    # Kirim atau perbarui embed di channel Discord di setiap server
    for guild in bot.guilds:
        channel = discord.utils.get(guild.channels, name=channel_name)

        if channel:
            # Jika pesan sudah ada, hapus pesan terakhir
            if livestream['slug'] in last_messages:
                last_message_id = last_messages[livestream['slug']]
    try:
        last_message = await channel.fetch_message(last_message_id)
        await last_message.edit(embed=embed)
        print(f"Perbarui notifikasi, Member yang sedang stream: {creator_name}")
    except discord.errors.NotFound:
        # The message no longer exists, send a new one
        sent_message = await channel.send(embed=embed)
        last_messages[livestream['slug']] = sent_message.id
        print(f"Message not found, sending a new notification for {creator_name}")
    else:
    # If the message ID is not in last_messages, send a new message
        sent_message = await channel.send(embed=embed)
    last_messages[livestream['slug']] = sent_message.id
    print(f"Notifikasi terkirim, Member yang sedang stream: {creator_name}")


def get_greeting(live_at):
    now = datetime.datetime.now(pytz.timezone('Asia/Jakarta'))

    # Parse the live_at string to a datetime object
    live_time = datetime.datetime.fromisoformat(live_at.replace('Z', '+00:00'))

    if 6 <= now.hour < 12:
        return "Selamat pagi"
    elif 12 <= now.hour < 15:
        return "Selamat siang"
    elif 15 <= now.hour < 20:
        return "Selamat sore"
    elif 20 <= now.hour < 24:
        return "Selamat malam"
    else:
        return "Selamat malam"

# Menjalankan bot
if __name__ == '__main__':
    print("Bot is starting...")
    bot.run('BOT_TOKEN')
