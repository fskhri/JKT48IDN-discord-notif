import discord
from discord.ext import commands
import requests

# Inisialisasi bot
bot = commands.Bot(command_prefix='$')

# Fungsi untuk mengambil data dari API
def get_livestream_data():
    api_url = 'https://mobile-api.idntimes.com/v3/livestreams'
    response = requests.get(api_url)
    
    # Menangani kesalahan saat mengambil data
    if response.status_code == 200:
        data = response.json()
        return {'data': data.get('data', [])}
    else:
        return {'error': f"Failed to fetch livestream data (Status Code: {response.status_code})"}

# Dictionary untuk menyimpan pesan yang terakhir di-edit untuk setiap live stream
last_messages = {}

# Fungsi yang dijalankan saat bot siap
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')
    await bot.change_presence(activity=discord.Game(name="Watching JKT48 Livestreams"))

# Fungsi untuk mengirimkan notifikasi atau memperbarui secara berkala
async def livestream_notification():
    livestream_data = get_livestream_data()

    if 'error' in livestream_data:
        print(livestream_data['error'])
        return

    if 'data' in livestream_data and len(livestream_data['data']) > 0:
        for livestream in livestream_data['data']:
            await send_livestream_notification(livestream)

# Fungsi untuk mengirimkan notifikasi ke channel Discord dengan embed
async def send_livestream_notification(livestream):
    channel_id = 1234567890  # Ganti dengan ID channel Discord Anda

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
    slug = livestream.get('slug', '')

    # Buat objek embed
    embed = discord.Embed(
        title=title,
        description=f"**Status:** {status}\n**Pemirsa:** {view_count}\n**Pembuat:** {creator_name}",
        color=discord.Color.green()  # Ganti warna sesuai keinginan
    )
    embed.set_thumbnail(url=thumbnail_url)  # Set thumbnail menggunakan URL

    # Tambahkan tombol untuk membuka playback dalam web player
    embed.add_field(name="Web Player", value=f"[Buka di Web Player]({playback_url})", inline=False)

    # Tambahkan tombol untuk membuka channel
    channel_url = f"https://www.idn.app/{username.lower()}/live/{slug}"
    embed.add_field(name="Channel", value=f"[Buka Channel]({channel_url})", inline=True)

    # Tambahkan ikon hadiah (gift) jika tersedia
    if gift_icon_url:
        embed.set_footer(text='Gift Icon', icon_url=gift_icon_url)

    # Tambahkan kategori livestream
    embed.add_field(name="Kategori", value=category_name, inline=True)

    # Kirim atau perbarui embed di channel Discord
    channel = bot.get_channel(channel_id)

    if livestream['room_identifier'] in last_messages:
        # Jika pesan sudah ada, hapus pesan terakhir
        last_message = await channel.fetch_message(last_messages[livestream['room_identifier']])
        await last_message.delete()

    # Kirim pesan baru
    sent_message = await channel.send(embed=embed)
    last_messages[livestream['room_identifier']] = sent_message.id

bot.remove_command('help')

# Command untuk menampilkan bantuan
@bot.command()
async def help(ctx):
    embed = discord.Embed(
        title='Bot Commands',
        description='Berikut adalah daftar perintah yang dapat digunakan:',
        color=discord.Color.blue()
    )
    embed.add_field(name='$stream_detail [member_name]', value='Menampilkan detail livestream untuk anggota tertentu.', inline=False)
    # Tambahkan field untuk command lain jika diperlukan

    await ctx.send(embed=embed)

# Command untuk melihat detail livestream dari anggota tertentu
@bot.command(name='stream_detail')
async def stream_detail(ctx, member_name):
    # Ambil data livestream terkini
    livestream_data = get_livestream_data()

    if 'error' in livestream_data:
        await ctx.send(livestream_data['error'])
        return

    if 'data' in livestream_data and len(livestream_data['data']) > 0:
        member_name_lower = member_name.lower()
        for livestream in livestream_data['data']:
            creator_name = livestream.get('creator', {}).get('name', '').lower()
            if member_name_lower in creator_name:
                # Ambil slug dari data livestream
                slug = livestream.get('slug', '')
                # Ambil username dari data livestream
                username = livestream.get('creator', {}).get('username', 'Unknown')

                # Buat objek embed untuk detail livestream
                embed = discord.Embed(
                    title=f"Detail Livestream untuk {member_name}",
                    description=f"**Judul:** {livestream['title']}\n"
                                f"**Status:** {livestream['status']}\n"
                                f"**Pemirsa:** {livestream['view_count']}\n"
                                f"**Kategori:** {livestream['category']['name']}\n"
                                f"**Username:** {username}\n"  # Tambahkan field username
                                f"**Web Player:** [Buka di Web Player]({livestream['playback_url']})\n"
                                f"**Slug:** {slug}",
                    color=discord.Color.blue()  # Ganti warna sesuai keinginan
                )

                # Tambahkan ikon hadiah (gift) jika tersedia
                gift_icon_url = livestream.get('gift_icon_url', '')
                if gift_icon_url:
                    embed.set_footer(text='Gift Icon', icon_url=gift_icon_url)

                # Tambahkan thumbnail jika tersedia
                thumbnail_url = livestream.get('thumbnail_url', '')
                if thumbnail_url:
                    embed.set_thumbnail(url=thumbnail_url)

                # Tambahkan tombol untuk membuka channel
                channel_url = f"https://www.idn.app/{username.lower()}/live/{slug}"
                embed.add_field(name="Channel", value=f"[Buka Channel]({channel_url})", inline=True)

                await ctx.send(embed=embed)
                return

        # Jika tidak ditemukan
        await ctx.send(f"Tidak ditemukan livestream untuk anggota dengan nama {member_name}.")

# Menjalankan bot
if __name__ == '__main__':
    bot.run('')
