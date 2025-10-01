# bot1.py
import asyncio
import importlib.util
import logging
import os
import platform
import signal
import socket
import sys
import threading

import discord
from discord.ext import commands
from dotenv import load_dotenv

from cogs.ticket import TicketActions, load_open_tickets, AssignedTicketActions
from utils.scheduler import align_and_start_standup, set_bot

load_dotenv()
BOT_TIER = "t1"  # TIER
TOKEN = os.getenv("DISCORD_TOKEN")
INTENTS = discord.Intents.default()
INTENTS.guilds = True
INTENTS.members = True
INTENTS.guild_messages = True
INTENTS.message_content = True

bot = commands.Bot(command_prefix="!", intents=INTENTS)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# to track if shutdown is in progress
shutdown_in_progress = False

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

try:
    from pyarmor_runtime_000000 import __pyarmor__
except ImportError:
    system = platform.system()
    fname = "pyarmor_runtime.pyd" if system == "Windows" else "pyarmor_runtime.so"
    path = os.path.join("pyarmor_runtime_000000", fname)
    spec = importlib.util.spec_from_file_location("__pyarmor__", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    __pyarmor__ = getattr(module, "__pyarmor__", None)


# Optional for satisfying Render
def start_dummy_server():
    port = int(os.environ.get("PORT", 10000))
    with socket.socket() as s:
        s.bind(("0.0.0.0", port))
        s.listen()
        while True:
            conn, _ = s.accept()
            conn.close()


threading.Thread(target=start_dummy_server, daemon=True).start()


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

            # Wait for tasks
            try:
                await asyncio.gather(*tasks, return_exceptions=True)
                logger.info('All tasks cancelled')
            except asyncio.CancelledError:
                logger.info('Tasks cancelled during shutdown')

        # Force close any remaining aiohttp conns
        try:
            import aiohttp
            import gc

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


logger = logging.getLogger(__name__)
shutdown_in_progress = False


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
        # Load license key
        license_key = os.getenv("LICENSE")
        if not license_key:
            print("❌ Missing LICENSE environment variable.")
            return

        # Validate license amd tier
        import aiohttp
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                        "https://license-api-production-b888.up.railway.app/validate",
                        json={"license_key": license_key}
                ) as resp:
                    result = await resp.json()

                    if not result.get("valid"):
                        print(f"❌ License invalid: {result.get('error')}")
                        return

                    # Compare server tier with hardcoded BOT_TIER
                    license_tier = result.get("tier")
                    if license_tier != BOT_TIER:
                        print(f"❌ License tier mismatch. Expected {BOT_TIER}, got {license_tier}")
                        return

                    print(f"✅ License valid for {BOT_TIER}. Expires: {result.get('expires')}")

        except Exception as e:
            print(f"❌ Failed to validate license: {e}")
            return

        # Load cogs
        cogs = ["cogs.standupconfig", "cogs.preview", "cogs.help", "cogs.notifying", "cogs.summary", "cogs.ticket"]
        for cog in cogs:
            try:
                await bot.load_extension(cog)
                print(f"{cog.split('.')[-1].capitalize()} cog loaded")
            except Exception as e:
                print(f"❌ Failed to load {cog}: {e}")

        # Start bot
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
