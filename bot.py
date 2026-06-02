import nextcord as discord
import asyncio
import aiohttp
import os
from datetime import datetime

# Config
DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN")
TIKTOK_USERNAME = "nagi_flippy"
CHANNEL_NAME = "🍈ㆍlive"
CHECK_INTERVAL = 60  # seconds between checks

ICON_URL = "https://raw.githubusercontent.com/filipkozlowski190907-bot/pppp/main/icon.png"
THUMBNAIL_URL = "https://raw.githubusercontent.com/filipkozlowski190907-bot/pppp/main/icon.png"

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

is_live = False


async def check_tiktok_live():
    url = f"https://www.tiktok.com/api/live/detail/?aid=1988&uniqueId={TIKTOK_USERNAME}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://www.tiktok.com/",
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    live_room = data.get("liveRoomUserInfo", {}).get("liveRoom", {})
                    status = live_room.get("status", 0)
                    return status == 2, live_room
    except Exception as e:
        print(f"Error checking TikTok: {e}")
    return False, {}


async def send_live_notification(channel, live_room):
    title = live_room.get("title", "Flippy's Live")
    live_url = f"https://www.tiktok.com/@{TIKTOK_USERNAME}/live"

    embed = discord.Embed(
        title=title,
        url=live_url,
        color=0x9B59B6
    )
    embed.set_author(name=TIKTOK_USERNAME, icon_url=ICON_URL)
    embed.set_image(url=THUMBNAIL_URL)
    embed.set_footer(text="TikTok Live")
    embed.timestamp = datetime.utcnow()

    await channel.send(
        content=f"@everyone Flippy just went live go show some love: {live_url} !",
        embed=embed
    )
    print(f"Sent live notification at {datetime.utcnow()}")


async def monitor_tiktok():
    global is_live

    await client.wait_until_ready()
    print(f"Monitoring TikTok: @{TIKTOK_USERNAME}")

    channel = None
    for guild in client.guilds:
        for ch in guild.text_channels:
            if CHANNEL_NAME in ch.name or ch.name in CHANNEL_NAME:
                channel = ch
                break
        if channel:
            break

    if not channel:
        print(f"Could not find channel: {CHANNEL_NAME}")
        print("Available channels:", [ch.name for guild in client.guilds for ch in guild.text_channels])
        return

    print(f"Found channel: #{channel.name}")

    while not client.is_closed():
        currently_live, live_room = await check_tiktok_live()

        if currently_live and not is_live:
            print("User just went live! Sending notification...")
            is_live = True
            await send_live_notification(channel, live_room)
        elif not currently_live and is_live:
            print("User went offline.")
            is_live = False

        await asyncio.sleep(CHECK_INTERVAL)


@client.event
async def on_ready():
    print(f"Bot is online as {client.user}")
    client.loop.create_task(monitor_tiktok())


client.run(DISCORD_TOKEN)
