import discord
from discord.ext import commands, tasks
import requests
import time
from urllib.parse import quote

# Inisialisasi bot
bot = commands.Bot(command_prefix='!')

CHANNEL_ID = 1234567890 # Ganti dengan ID channel Discord Anda

# Fungsi untuk mengambil data dari API
def get_livestream_data():
    api_url = 'https://mobile-api.idntimes.com/v3/livestreams'
    response = requests.get(api_url)
    data = response.json()

    # Filter data untuk mendapatkan livestream yang hanya terkait dengan user JKT48
    jkt48_livestreams = [livestream for livestream in data.get('data', []) if 'jkt48' in livestream.get('creator', {}).get('username', '').lower()]

    return {'data': jkt48_livestreams}

# Dictionary untuk menyimpan pesan yang terakhir di-edit untuk setiap live stream
last_messages = {}

# Pengecekan livestream selesai
@tasks.loop(minutes=1)
async def check_finished_streams():
    livestream_data = get_livestream_data()

    if 'data' in livestream_data and len(livestream_data['data']) > 0:
        for livestream in livestream_data['data']:
            if livestream['status'].lower() == 'ended':
                member_name = livestream.get('creator', {}).get('name', 'Unknown')
                channel_id = CHANNEL_ID
                channel = bot.get_channel(channel_id)
                await channel.send(f"Terima kasih kepada {member_name} yang sudah menyelesaikan livestreamnya! Channel: {live_streams.get(member_name, 'N/A')}")
                print(f"Notifikasi terkirim ke server atas nama {member_name}")

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
        for livestream in livestream_data['data']:
            await send_livestream_notification(livestream)

# Fungsi untuk mengirimkan notifikasi ke channel Discord dengan embed
async def send_livestream_notification(livestream):
    channel_id = CHANNEL_ID  # Ganti dengan ID channel Discord Anda

    # Proses data sesuai kebutuhan
    title = livestream.get('title', 'No Title')
    playback_url = livestream.get('playback_url', '')
    thumbnail_url = livestream.get('image_url', '')
    view_count = livestream.get('view_count', 0)
    status = livestream.get('status', 'Unknown')
    creator = livestream.get('creator', {})
    creator_name = creator.get('name', 'Unknown')
    username = creator.get('username', 'Unknown')
    gift_icon_url = livestream.get('gift_icon_url', '')
    category_name = livestream.get('category', {}).get('name', 'Unknown')
    slug = livestream.get('slug', '')

    # Retrieve total gold from live_stream_stats
    total_gold = live_stream_stats.get(creator_name, {}).get('total_gold', 0)

    # Buat objek embed
    embed = discord.Embed(
        title=title,
        description=f"**Status:** {status}\n**Pemirsa 👥:** {view_count}\n**Pembuat:** {creator_name}",
        color=discord.Color.green()  # Ganti warna sesuai keinginan
    )
    embed.set_thumbnail(url=thumbnail_url)

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
    channel = bot.get_channel(channel_id)

    if livestream['room_identifier'] in last_messages:
        # Jika pesan sudah ada, hapus pesan terakhir
        last_message = await channel.fetch_message(last_messages[livestream['room_identifier']])
        await last_message.delete()

    # Kirim pesan baru
    sent_message = await channel.send(embed=embed)
    last_messages[livestream['room_identifier']] = sent_message.id
    print(f"Notifikasi terkirim, Member yang sedang stream: {creator_name}")

# Menjalankan bot
if __name__ == '__main__':
    bot.run('BOT_TOKEN')
