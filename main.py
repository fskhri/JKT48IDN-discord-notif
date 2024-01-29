import discord
from discord.ext import commands, tasks
import requests
import time
import datetime
import random

channel_name = 'IDN NOTIFER' # Ganti ini dengan room discord kamu

# Inisialisasi bot
bot = commands.Bot(command_prefix='!')

# Fungsi untuk mengambil data dari API
def get_livestream_data():
    api_url = 'https://mobile-api.idntimes.com/v3/livestreams'
    response = requests.get(api_url)
    data = response.json()

    # Filter data untuk mendapatkan livestream yang hanya terkait dengan user JKT48
    jkt48_livestreams = [livestream for livestream in data.get('data', []) if 'JKT48' in livestream.get('creator', {}).get('username', '').lower() or 'jkt48' in livestream.get('creator', {}).get('username', '').lower()]

    return {'data': jkt48_livestreams}

# Dictionary untuk menyimpan pesan yang terakhir di-edit untuk setiap live stream
last_messages = {}

# Before the on_ready event, define live_stream_stats as an empty dictionary
live_stream_stats = {}

# Pengecekan livestream selesai
@tasks.loop(minutes=1)
async def check_finished_streams():
    print("Checking finished streams...")
    livestream_data = get_livestream_data()

    if 'data' in livestream_data and len(livestream_data['data']) > 0:
        for livestream in livestream_data['data']:
            if livestream['status'].lower() == 'ended':
                print(f"Detected ended livestream: {livestream}")
                member_name = livestream.get('creator', {}).get('name', 'Unknown')
                channel_id = channel_name
                channel = bot.get_channel(channel_id)

                # Menghitung total jam live stream
                start_time = livestream.get('started_at', 0)
                end_time = livestream.get('ended_at', 0)
                duration_seconds = end_time - start_time
                duration_minutes, duration_seconds = divmod(duration_seconds, 60)
                duration_hours, duration_minutes = divmod(duration_minutes, 60)

                # Membuat pesan ringkasan livestream
                summary_message = (
                    f"Live {member_name} telah berakhir.\n"
                    f"{member_name} mewarnai harimu selama "
                    f"{duration_hours:02}:{duration_minutes:02}:{duration_seconds:02}\n\n"
                    f"Start: {livestream.get('started_at_formatted', 'Unknown')}\n"
                    f"End: {livestream.get('ended_at_formatted', 'Unknown')}\n\n"
                    f"👥 {livestream.get('view_count', 0)}\n"
                    f"💬 {livestream.get('comment_count', 0)}"
                )

                # Mengirim pesan ringkasan ke channel Discord
                await channel.send(summary_message)

                print(f"Notifikasi terkirim ke server atas nama {member_name}")
    else:
        # If no livestream data is available, it means the member has finished streaming
        # You can add your "finish stream" logic here
        print("No livestream data available. The member has finished streaming.")

# Fungsi yang dijalankan saat bot siap
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="JKT48 Livestreams"))
    
    # Memulai pengecekan livestream selesai
    check_finished_streams.start()

    # Loop utama
    while True:
        await livestream_notification()
        time.sleep(100)  # Tunggu 5 menit sebelum memeriksa lagi

# Fungsi untuk mengirimkan notifikasi atau memperbarui secara berkala
async def livestream_notification():
    livestream_data = get_livestream_data()

    if livestream_data and 'data' in livestream_data and len(livestream_data['data']) > 0:
        print("Livestream data available. Sending notifications...")
        for livestream in livestream_data['data']:
            await send_livestream_notification(livestream)

                # Example: Populate live_stream_stats (replace this with your actual logic)
    for livestream in get_livestream_data()['data']:
        creator_name = livestream.get('creator', {}).get('name', 'Unknown')
        live_stream_stats[creator_name] = {'total_gold': 0}

# Fungsi untuk mengirimkan notifikasi ke channel Discord dengan embed
async def send_livestream_notification(livestream):
    channel_name = channel_name  # Ganti dengan ID channel Discord Anda

    random_color = discord.Color(random.randint(0, 0xFFFFFF)) # Random Color For Embed

    # Proses data sesuai kebutuhan
    title = livestream.get('title', 'No Title')
    playback_url = livestream.get('playback_url', '')
    thumbnail_url = livestream.get('image_url', '')  # Ganti dengan field yang sesuai, bisa 'image_url' atau 'thumbnail_url'
    view_count = livestream.get('view_count', 0)
    status = livestream.get('status', 'Unknown')
    creator = livestream.get('creator', {})
    creator_name = creator.get('name', 'Unknown')
    username = creator.get('username', 'Unknown')  # Tambahan untuk username
    gift_icon_url = livestream.get('gift_icon_url', '')
    category_name = livestream.get('category', {}).get('name', 'Unknown')
    slug = livestream.get('slug', '')  # Ganti dengan field yang sesuai
    live_at = livestream.get('live_at', '')
    greeting = get_greeting(live_at)

    # Retrieve total gold from live_stream_stats
    total_gold = live_stream_stats.get(creator_name, {}).get('total_gold', 0)

    # Buat objek embed
    embed = discord.Embed(
        title=title,
        description=f"{greeting}, si {creator_name} lagi live nih! Nonton yuk! 🎥\n"
                    f"**Pemirsa 👥:** {view_count}\n"
                    f"**Pembuat:** {creator_name}",
        color=random_color  # Ganti warna sesuai keinginan
    )
    embed.set_thumbnail(url=thumbnail_url)  # Set thumbnail menggunakan URL

    # Tambahkan tombol untuk membuka playback dalam web player
    embed.add_field(name="Web Player", value=f"[Buka di Web Player]({playback_url})", inline=False)

    # Tambahkan tombol untuk membuka channel
    channel_url = f"https://www.idn.app/{username.lower().replace(' ', '')}/live/{slug}"
    embed.add_field(name="Channel", value=f"[Buka Channel]({channel_url})", inline=True)

    # Tambahkan ikon hadiah (gift) jika tersedia
    if gift_icon_url:
        embed.set_footer(text='Gift Icon')
        embed.set_footer(icon_url=gift_icon_url)

    # Tambahkan kategori livestream
    embed.add_field(name="Kategori", value=category_name, inline=True)

    # Tambahkan total gold
    embed.add_field(name="Total Gold", value=total_gold, inline=True)

    # Kirim atau perbarui embed di channel Discord
    channel = bot.get_channel(channel_name)

    if livestream['room_identifier'] in last_messages:
        # Jika pesan sudah ada, hapus pesan terakhir
        last_message = await channel.fetch_message(last_messages[livestream['room_identifier']])
        await last_message.delete()

    # Kirim pesan baru
    sent_message = await channel.send(embed=embed)
    last_messages[livestream['room_identifier']] = sent_message.id
    print(f"Notifikasi terkirim, Member yang sedang stream: {creator_name}")

def get_greeting(live_at):
    now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=7)))

    # Convert epoch timestamp to datetime object
    live_time = datetime.datetime.utcfromtimestamp(int(live_at))
    live_time = live_time.replace(tzinfo=datetime.timezone.utc)
    live_time = live_time.astimezone(datetime.timezone(datetime.timedelta(hours=7)))

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