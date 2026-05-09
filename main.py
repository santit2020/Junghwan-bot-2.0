import asyncio
import logging
import os
import sys
from aiohttp import web
from bot.telegram_bot import TelegramBot
from config.settings import Settings


def setup_logging():
    log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
    logging.basicConfig(
        level=getattr(logging, log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('bot.log', mode='a', encoding='utf-8')
        ]
    )
    logging.getLogger('aiogram').setLevel(logging.WARNING)
    logging.getLogger('aiohttp').setLevel(logging.WARNING)


async def health_check(request):
    return web.json_response({
        "status": "healthy",
        "service": "Junghwan Telegram Bot",
        "version": "2.0.0",
        "timestamp": asyncio.get_event_loop().time()
    })


async def bot_info(request):
    settings = Settings()
    return web.json_response({
        "bot_name": settings.BOT_NAME,
        "owner": settings.BOT_OWNER_NAME,
    })


async def create_health_server():
    app = web.Application()
    app.router.add_get('/health', health_check)
    app.router.add_get('/', health_check)
    app.router.add_get('/info', bot_info)
    port = int(os.getenv('PORT', 5000))
    runner = web.AppRunner(app)
    await runner.setup()
    try:
        site = web.TCPSite(runner, '0.0.0.0', port)
        await site.start()
        logging.info(f"Health server started on port {port}")
        return runner
    except OSError as e:
        if e.errno == 98:
            site = web.TCPSite(runner, '0.0.0.0', port + 1)
            await site.start()
            return runner
        raise


async def main():
    setup_logging()
    logger = logging.getLogger(__name__)

    try:
        settings = Settings()
        settings.validate()

        logger.info("Starting Junghwan Telegram Bot v2.0")

        # Wait so the previous instance fully releases Telegram polling
        # before we connect — prevents TelegramConflictError on Render
        logger.info("Waiting 8s for previous instance to shut down...")
        await asyncio.sleep(8)

        health_runner = await create_health_server()

        bot = TelegramBot(settings)
        try:
            await bot.start_polling()
        except Exception as e:
            logger.error(f"Bot polling error: {e}")
            raise
        finally:
            await health_runner.cleanup()

    except Exception as e:
        logger.error(f"Critical error during bot startup: {e}")
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Bot stopped by user (Ctrl+C)")
    except Exception as e:
        logging.error(f"Bot crashed: {e}")
        sys.exit(1)
