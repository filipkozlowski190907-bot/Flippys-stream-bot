import hikari
import asyncio
import os
from datetime import datetime
from TikTokLive import TikTokLiveClient
from TikTokLive.events import ConnectEvent, DisconnectEvent

DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN")
TIKTOK_USERNAME = "nagi_flippy"
CHANNEL_ID = 1510902215962001419

ICON_URL = "https://raw.githubusercontent.com/filipkozlowski190907-bot/pppp/main/icon.png"
THUMBNAIL_URL = "https://raw.githubusercontent.com/filipkozlowski190907-bot/pppp/main/icon.png"

bot = hikari.GatewayBot(token=DISCORD_TOKEN)
notification_sent = False
currently_live = False


async def send_live_notification(title="Flippy's Live"):
    global notification_sent
    if notification_sent:
        print("Notification already sent, skipping.")
        return
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
        content=f"<@&1492978052525981707> Flippy just went live go show some love: {live_url} !",
        embed=embed
    )
    notification_sent = True
    print(f"Sent live notification at {datetime.utcnow()}")


async def monitor_tiktok():
    global notification_sent, currently_live

    print(f"Starting TikTok monitor for @{TIKTOK_USERNAME}")

    while True:
        try:
            client = TikTokLiveClient(unique_id=f"@{TIKTOK_USERNAME}")

            @client.on(ConnectEvent)
            async def on_connect(event: ConnectEvent):
                global currently_live
                print("Connected to live stream!")
                currently_live = True
                await send_live_notification()

            @client.on(DisconnectEvent)
            async def on_disconnect(event: DisconnectEvent):
                global notification_sent, currently_live
                print("Stream ended. Resetting.")
                notification_sent = False
                currently_live = False

            print("Connecting to TikTok live...")
            await client.start()

        except Exception as e:
            print(f"Not live or connection error: {e}")
            # Only reset if they weren't live (i.e. connection failed, not stream ended)
            if not currently_live:
                notification_sent = False
            await asyncio.sleep(60)


@bot.listen(hikari.StartedEvent)
async def on_started(event):
    print(f"Bot is online!")
    asyncio.create_task(monitor_tiktok())


bot.run()
