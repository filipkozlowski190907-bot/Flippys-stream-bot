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
    # Use webcast API to check live status
    url = f"https://webcast.tiktok.com/webcast/room/check_alive/?aid=1988&app_language=en&app_name=tiktok_web&browser_language=en&browser_name=Mozilla&browser_online=true&browser_platform=Win32&browser_version=5.0&channel=tiktok_web&cookie_enabled=true&device_platform=web_pc&focus_state=true&from_page=user&history_len=2&is_fullscreen=false&is_page_visible=true&room_id=&unique_id={TIKTOK_USERNAME}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": f"https://www.tiktok.com/@{TIKTOK_USERNAME}/live",
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            # First get the room ID from the user's page
            profile_url = f"https://www.tiktok.com/api/user/detail/?aid=1988&uniqueId={TIKTOK_USERNAME}&msToken=&X-Bogus="
            
            # Try checking via tiktok-live-connector style API
            check_url = f"https://webcast.tiktok.com/webcast/room/info/?aid=1988&app_language=en&app_name=tiktok_web&browser_language=en&browser_name=Mozilla&browser_online=true&browser_platform=Win32&browser_version=5.0&channel=tiktok_web&cookie_enabled=true&device_platform=web_pc&focus_state=true&from_page=user&history_len=2&is_fullscreen=false&is_page_visible=true&room_id=&unique_id={TIKTOK_USERNAME}"
            
            async with session.get(check_url, headers=headers, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                print(f"Webcast API status: {resp.status}")
                if resp.status == 200:
                    data = await resp.json()
                    print(f"Webcast response: {str(data)[:300]}")
                    status = data.get("data", {}).get("status", 0)
                    print(f"Room status: {status}")
                    # status 2 = live, 4 = ended
                    return status == 2, data.get("data", {})
                else:
                    text = await resp.text()
                    print(f"Webcast error: {text[:200]}")
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
                print("User is live! Sending notification...")
                try:
                    await send_live_notification(live_room)
                    notification_sent = True
                    print("Notification sent successfully!")
                except Exception as e:
                    print(f"Failed to send notification, retrying in {RETRY_INTERVAL}s: {e}")
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
