# bot.py
import logging
import os

import discord
from discord.ext import commands
from dotenv import load_dotenv

from cogs.ticket import TicketActions, load_open_tickets, AssignedTicketActions
from scheduler import align_and_start_standup, set_bot

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
INTENTS = discord.Intents.default()
INTENTS.guilds = True
INTENTS.members = True
INTENTS.guild_messages = True
INTENTS.message_content = True

bot = commands.Bot(command_prefix="!", intents=INTENTS)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variable to track if shutdown is in progress
shutdown_in_progress = False


@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅ Logged in as {bot.user.name}")
    set_bot(bot)

    # Start ticket restoration in background with rate limiting
    asyncio.create_task(restore_ticket_views())

    await align_and_start_standup()


async def restore_ticket_views():
    """Register persistent views for all open tickets without editing messages."""
    tickets = load_open_tickets()
    print(f"Registering persistent views for {len(tickets)} tickets...")

    for ticket in tickets:
        try:
            ticket_id = ticket["id"]
            assigned = bool(ticket.get("assigned_to") or ticket.get("assigned_role"))

            # Pick the correct view class based on ticket state
            if assigned:
                view = AssignedTicketActions(ticket_id)
            else:
                view = TicketActions(ticket_id)

            bot.add_view(view)
            print(f"✅ Registered view for ticket {ticket_id}")

        except Exception as e:
            print(f"❌ Failed to register view for ticket {ticket['id']}: {e}")

    print("View registration complete.")


async def shutdown_handler(signal_received=None, frame=None):
    """Handle shutdown signals gracefully"""
    global shutdown_in_progress

    if shutdown_in_progress:
        logger.info("Shutdown already in progress, ignoring signal")
        return

    shutdown_in_progress = True
    logger.info(f'Starting graceful shutdown...')

    try:
        # Close the bot connection properly
        if not bot.is_closed():
            logger.info('Closing bot connection...')
            await bot.close()
            logger.info('Bot connection closed successfully')

        # Cancel all running tasks
        tasks = [task for task in asyncio.all_tasks() if task is not asyncio.current_task()]
        if tasks:
            logger.info(f'Cancelling {len(tasks)} running tasks...')
            for task in tasks:
                task.cancel()

            # Wait for tasks to complete cancellation
            try:
                await asyncio.gather(*tasks, return_exceptions=True)
                logger.info('All tasks cancelled')
            except asyncio.CancelledError:
                logger.info('Tasks cancelled during shutdown')

        # Force close any remaining aiohttp connections
        try:
            import aiohttp
            import gc

            # Close any remaining aiohttp connectors
            for obj in gc.get_objects():
                if isinstance(obj, aiohttp.connector.BaseConnector):
                    if not obj.closed:
                        await obj.close()
        except Exception as e:
            logger.debug(f'Error cleaning up aiohttp connections: {e}')

    except asyncio.CancelledError:
        logger.info('Shutdown interrupted by cancellation')
    except Exception as e:
        logger.error(f'Error during shutdown: {e}')

    logger.info('Shutdown complete')


import asyncio
import signal
import sys
import logging
import discord

logger = logging.getLogger(__name__)
shutdown_in_progress = False


# Assume your bot instance is already defined somewhere above as `bot`

async def main():
    global shutdown_in_progress

    # Signal handling (graceful shutdown)
    if sys.platform != 'win32':
        loop = asyncio.get_event_loop()
        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(sig, lambda s=sig: asyncio.create_task(shutdown_handler(s, None)))
    else:
        signal.signal(signal.SIGINT, lambda s, f: asyncio.create_task(shutdown_handler(s, f)))

    try:
        # 🔐 Step 1: Load license key
        try:
            with open("license.txt", "r") as f:
                license_key = f.read().strip()
        except FileNotFoundError:
            print("❌ Missing license.txt file")
            return

        # 🔍 Step 2: Validate license
        import aiohttp
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                        "https://license-api-production-b888.up.railway.app/validate",
                        json={
                            "license_key": license_key
                        }
                ) as resp:
                    result = await resp.json()
                    if not result.get("valid"):
                        print(f"❌ License invalid: {result.get('error')}")
                        return
                    else:
                        print(f"✅ License valid. Expires: {result.get('expires')}")
        except Exception as e:
            print(f"❌ Failed to validate license: {e}")
            return

        # 📦 Step 3: Load cogs
        cogs = ["cogs.standupconfig", "cogs.preview", "cogs.help", "cogs.notifying", "cogs.summary", "cogs.ticket"]
        for cog in cogs:
            try:
                await bot.load_extension(cog)
                print(f"{cog.split('.')[-1].capitalize()} cog loaded")
            except Exception as e:
                print(f"❌ Failed to load {cog}: {e}")

        # 🚀 Step 4: Start bot
        logger.info('Starting bot...')
        await bot.start(TOKEN)

    except KeyboardInterrupt:
        logger.info('Received keyboard interrupt')
        if not shutdown_in_progress:
            await shutdown_handler(signal.SIGINT, None)

    except discord.LoginFailure:
        logger.error('Invalid bot token')

    except discord.HTTPException as e:
        logger.error(f'HTTP error: {e}')

    except Exception as e:
        logger.error(f'Unexpected error: {e}')

    finally:
        if not bot.is_closed():
            logger.info('Ensuring bot connection is closed...')
            try:
                await bot.close()
            except asyncio.CancelledError:
                pass

        # aiohttp connector cleanup
        try:
            import gc
            for obj in gc.get_objects():
                if isinstance(obj, aiohttp.connector.BaseConnector):
                    if not obj.closed:
                        await obj.close()
        except Exception:
            pass


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info('Program interrupted by user')
    except Exception as e:
        logger.error(f'Fatal error: {e}')
    finally:
        logger.info('Program terminated')
