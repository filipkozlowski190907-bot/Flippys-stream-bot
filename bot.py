import hikari
import asyncio
import aiohttp
import os
from datetime import datetime

DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN")
TIKTOK_USERNAME = "nagi_flippy"
CHANNEL_ID = 1510902215962001419
CHECK_INTERVAL = 60

ICON_URL = "https://raw.githubusercontent.com/filipkozlowski190907-bot/pppp/main/icon.png"
THUMBNAIL_URL = "https://raw.githubusercontent.com/filipkozlowski190907-bot/pppp/main/icon.png"

bot = hikari.GatewayBot(token=DISCORD_TOKEN)
is_live = False


async def check_tiktok_live():
    url = f"https://www.tiktok.com/api/live/detail/?aid=1988&uniqueId={TIKTOK_USERNAME}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
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


async def send_live_notification(live_room):
    title = live_room.get("title", "Flippy's Live")
    live_url = f"https://www.tiktok.com/@{TIKTOK_USERNAME}/live"

    embed = hikari.Embed(
        title=title,
        url=live_url,
        color=0x9B59B6,
        timestamp=datetime.utcnow()
    )
    embed.set_author(name=TIKTOK_USERNAME, icon=ICON_URL)
    embed.set_image(THUMBNAIL_URL)
    embed.set_footer("TikTok Live")

    await bot.rest.create_message(
        CHANNEL_ID,
        content=f"@everyone Flippy just went live go show some love: {live_url} !",
        embed=embed
    )
    print(f"Sent live notification at {datetime.utcnow()}")


async def monitor_tiktok():
    global is_live

    await asyncio.sleep(5)
    print(f"Monitoring TikTok: @{TIKTOK_USERNAME}")
    print(f"Sending to channel ID: {CHANNEL_ID}")

    while True:
        currently_live, live_room = await check_tiktok_live()

        if currently_live and not is_live:
            print("User just went live! Sending notification...")
            is_live = True
            await send_live_notification(live_room)
        elif not currently_live and is_live:
            print("User went offline.")
            is_live = False

        await asyncio.sleep(CHECK_INTERVAL)


@bot.listen(hikari.StartedEvent)
async def on_started(event):
    print(f"Bot is online!")
    asyncio.create_task(monitor_tiktok())


bot.run()
