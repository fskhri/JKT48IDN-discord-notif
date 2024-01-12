import discord
from discord.ext import commands, tasks
import requests

# Inisialisasi bot
bot = commands.Bot(command_prefix='!')

# Fungsi untuk mengirimkan notifikasi ke channel Discord dengan embed
# Fungsi untuk mengambil data dari API
def get_livestream_data():
    api_url = 'https://mobile-api.idntimes.com/v3/livestreams'
    response = requests.get(api_url)
    data = response.json()

    # Filter data untuk mendapatkan livestream yang hanya terkait dengan user JKT48
    jkt48_livestreams = [livestream for livestream in data.get('data', []) if 'jkt48' in livestream.get('creator', {}).get('username', '').lower()]

    return {'data': jkt48_livestreams}

# Fungsi untuk mengirimkan notifikasi ke channel Discord dengan embed
async def send_livestream_notification():
    channel_id = 123456789  # Ganti dengan ID channel Discord Anda

    livestream_data = get_livestream_data()

    if livestream_data and 'data' in livestream_data and len(livestream_data['data']) > 0:
        # Ambil data livestream pertama
        livestream = livestream_data['data'][0]

        # Proses data sesuai kebutuhan
        title = livestream.get('title', 'No Title')
        thumbnail_url = livestream.get('image_url', '')  # Ganti dengan field yang sesuai, bisa 'image_url' atau 'thumbnail_url'
        view_count = livestream.get('view_count', 0)
        status = livestream.get('status', 'Unknown')
        creator_name = livestream.get('creator', {}).get('name', 'Unknown')

        # Buat objek embed
        embed = discord.Embed(
            title=title,
            description=f"**Status:** {status}\n**Pemirsa:** {view_count}\n**Pembuat:** {creator_name}",
            color=discord.Color.green()  # Ganti warna sesuai keinginan
        )
        embed.set_thumbnail(url=thumbnail_url)  # Set thumbnail menggunakan URL
        embed.add_field(name="Web Player", value=f"[Buka di Web Player]({livestream['playback_url']})", inline=False)

        # Kirim embed ke channel Discord
        channel = bot.get_channel(channel_id)
        await channel.send(embed=embed)


# Fungsi yang dijalankan saat bot siap
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')

    # Jalankan task secara berkala (misalnya, setiap 5 menit)
    livestream_notification.start()

# Task untuk mengirimkan notifikasi secara berkala
@tasks.loop(minutes=5)
async def livestream_notification():
    await send_livestream_notification()

# Command untuk mengirim test embed
@bot.command(name='test_embed')
async def test_embed(ctx):
    # Buat objek embed untuk diuji
    test_embed = discord.Embed(
        title='Ini adalah test embed',
        description='Ini adalah deskripsi dari test embed.',
        color=discord.Color.blue()
    )
    test_embed.add_field(name='Field 1', value='Isi dari Field 1', inline=False)
    test_embed.add_field(name='Field 2', value='Isi dari Field 2', inline=True)
    test_embed.set_footer(text='Ini adalah footer dari test embed.')

    # Tambahkan informasi kategori JKT48 pada test embed
    test_embed.add_field(name="Kategori", value="JKT48", inline=True)

    # Kirim embed ke channel yang memanggil perintah
    sent_message = await ctx.send(embed=test_embed)

    # Tambahkan reaction sebagai contoh
    await sent_message.add_reaction('👍')
    await sent_message.add_reaction('👎')

# Menjalankan bot
if __name__ == '__main__':
    bot.run('TOKEN BOT')
