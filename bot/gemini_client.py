import asyncio
import logging
import os
import sys
from aiohttp import web
from bot.telegram_bot import TelegramBot
from config.settings import Settings

# Configure logging
def setup_logging():
    """Setup comprehensive logging configuration"""
    log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
    logging.basicConfig(
        level=getattr(logging, log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('bot.log', mode='a', encoding='utf-8')
        ]
    )
    
    # Set specific loggers
    logging.getLogger('aiogram').setLevel(logging.WARNING)
    logging.getLogger('aiohttp').setLevel(logging.WARNING)

async def health_check(request):
    """Health check endpoint for deployment platforms."""
    return web.json_response({
        "status": "healthy",
        "service": "Junghwan Telegram Bot",
        "version": "2.0.0",
        "timestamp": asyncio.get_event_loop().time()
    })

async def bot_info(request):
    """Bot information endpoint"""
    settings = Settings()
    return web.json_response({
        "bot_name": settings.BOT_NAME,
        "owner": settings.BOT_OWNER_NAME,
        "features": [
            "Natural conversation with Gemini AI",
            "Group and private chat support", 
            "Broadcasting system",
            "Personality-driven responses",
            "Multi-language support"
        ]
    })

async def create_health_server():
    """Create a simple HTTP server for health checks and monitoring."""
    app = web.Application()
    app.router.add_get('/health', health_check)
    app.router.add_get('/', health_check)
    app.router.add_get('/info', bot_info)
    
    # Get port from environment (Replit uses port 5000)
    port = int(os.getenv('PORT', 5000))
    
    runner = web.AppRunner(app)
    await runner.setup()
    
    try:
        site = web.TCPSite(runner, '0.0.0.0', port)
        await site.start()
        logging.info(f"Health server started on port {port}")
        return runner
    except OSError as e:
        if e.errno == 98:  # Address already in use
            logging.error(f"Port {port} is already in use. Trying port {port + 1}")
            site = web.TCPSite(runner, '0.0.0.0', port + 1)
            await site.start()
            logging.info(f"Health server started on port {port + 1}")
            return runner
        else:
            raise

async def main():
    """Main entry point for the Telegram bot."""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        # Initialize settings and validate environment
        settings = Settings()
        settings.validate()
        
        logger.info("Starting Junghwan Telegram Bot v2.0")
        logger.info(f"Bot Name: {settings.BOT_NAME}")
        logger.info(f"Owner: {settings.BOT_OWNER_NAME}")
        
        # Start health server for deployment monitoring
        health_runner = await create_health_server()
        logger.info("Health monitoring server started")
        
        # Initialize and start the bot
        bot = TelegramBot(settings)
        
        try:
            # Start bot polling
            await bot.start_polling()
        except Exception as e:
            logger.error(f"Bot polling error: {e}")
            raise
        finally:
            # Clean up health server
            await health_runner.cleanup()
            logger.info("Health server stopped")
            
    except Exception as e:
        logger.error(f"Critical error during bot startup: {e}")
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Bot stopped by user (Ctrl+C)")
    except Exception as e:
        logging.error(f"Bot crashed with error: {e}")
        sys.exit(1)
