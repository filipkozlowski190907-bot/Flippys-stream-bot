import hikari
import asyncio
import aiohttp
import os
from datetime import datetime

DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN")
TIKTOK_USERNAME = "nagi_flippy"
CHANNEL_ID = 1510902215962001419
CHECK_INTERVAL = 60
RETRY_INTERVAL = 15

ICON_URL = "https://raw.githubusercontent.com/filipkozlowski190907-bot/pppp/main/icon.png"
THUMBNAIL_URL = "https://raw.githubusercontent.com/filipkozlowski190907-bot/pppp/main/icon.png"

bot = hikari.GatewayBot(token=DISCORD_TOKEN)
is_live = False
notification_sent = False


async def check_tiktok_live():
    url = f"https://www.tiktok.com/@{TIKTOK_USERNAME}/live"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Referer": "https://www.tiktok.com/",
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=15), allow_redirects=True) as resp:
                print(f"TikTok page status: {resp.status}, final URL: {resp.url}")
                text = await resp.text()
                
                # If redirected away from /live, they're not live
                if "/live" not in str(resp.url):
                    print("Redirected away from /live — not live")
                    return False, {}
                
                # Check for live indicators in the page
                live_indicators = [
                    '"isLive":true',
                    '"is_live":true', 
                    'LIVE_STREAMING',
                    '"liveRoomInfo"',
                    'webcast/room'
                ]
                
                for indicator in live_indicators:
                    if indicator in text:
                        print(f"Live indicator found: {indicator}")
                        return True, {"title": "Flippy's Live"}
                
                print("No live indicators found in page")
                return False, {}
                
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
    global is_live, notification_sent

    await asyncio.sleep(5)
    print(f"Monitoring TikTok: @{TIKTOK_USERNAME}")
    print(f"Sending to channel ID: {CHANNEL_ID}")

    while True:
        currently_live, live_room = await check_tiktok_live()

        if currently_live:
            is_live = True
            if not notification_sent:
                print("User is live and notification not yet sent — attempting...")
                try:
                    await send_live_notification(live_room)
                    notification_sent = True
                    print("Notification sent successfully!")
                except Exception as e:
                    print(f"Failed to send notification, will retry in {RETRY_INTERVAL}s: {e}")
                    await asyncio.sleep(RETRY_INTERVAL)
                    continue
        else:
            if is_live:
                print("User went offline. Resetting.")
            is_live = False
            notification_sent = False

        await asyncio.sleep(CHECK_INTERVAL)


@bot.listen(hikari.StartedEvent)
async def on_started(event):
    print(f"Bot is online!")
    asyncio.create_task(monitor_tiktok())


bot.run()
