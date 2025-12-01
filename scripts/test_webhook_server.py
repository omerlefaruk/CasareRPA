"""
Simple webhook test server for testing Cloudflare Tunnel.
Runs on port 8766 to receive webhooks at https://webhooks.casare.net

Usage:
    python scripts/test_webhook_server.py
"""

import asyncio
from aiohttp import web
from loguru import logger
from datetime import datetime


async def handle_health(request):
    """Health check endpoint."""
    return web.json_response(
        {
            "status": "healthy",
            "service": "casare-rpa-webhooks",
            "timestamp": datetime.utcnow().isoformat(),
        }
    )


async def handle_webhook(request):
    """Handle any webhook POST request."""
    path = request.path

    # Read body
    try:
        body = await request.json()
    except Exception:
        body = await request.text()

    # Log the webhook
    logger.info("Webhook received!")
    logger.info(f"  Path: {path}")
    logger.info(f"  Method: {request.method}")
    logger.info(f"  Headers: {dict(request.headers)}")
    logger.info(f"  Body: {body}")

    return web.json_response(
        {
            "status": "received",
            "path": path,
            "method": request.method,
            "timestamp": datetime.utcnow().isoformat(),
            "body_received": body if isinstance(body, dict) else str(body)[:100],
        }
    )


async def handle_any(request):
    """Catch-all handler for any method."""
    return await handle_webhook(request)


def create_app():
    """Create the aiohttp application."""
    app = web.Application()

    # Health check
    app.router.add_get("/health", handle_health)

    # Webhook endpoints (match TriggerManager patterns)
    app.router.add_post("/hooks/{trigger_id}", handle_webhook)
    app.router.add_route("*", "/webhooks/{path:.*}", handle_any)

    # Catch-all for testing
    app.router.add_route("*", "/{path:.*}", handle_any)

    return app


async def main():
    """Run the webhook test server."""
    app = create_app()
    runner = web.AppRunner(app)
    await runner.setup()

    # Bind to 0.0.0.0 so Cloudflare Tunnel can reach it
    site = web.TCPSite(runner, "0.0.0.0", 8766)
    await site.start()

    logger.info("=" * 50)
    logger.info("Webhook Test Server Started")
    logger.info("=" * 50)
    logger.info("")
    logger.info("Local:  http://localhost:8766")
    logger.info("Tunnel: https://webhooks.casare.net")
    logger.info("")
    logger.info("Endpoints:")
    logger.info("  GET  /health              - Health check")
    logger.info("  POST /hooks/{id}          - Webhook by ID")
    logger.info("  POST /webhooks/{path}     - Webhook by path")
    logger.info("  *    /{anything}          - Catch-all (for testing)")
    logger.info("")
    logger.info("Test with:")
    logger.info(
        '  curl -X POST https://webhooks.casare.net/test -H "Content-Type: application/json" -d \'{"hello":"world"}\''
    )
    logger.info("")
    logger.info("Press Ctrl+C to stop")
    logger.info("=" * 50)

    # Keep running
    try:
        while True:
            await asyncio.sleep(3600)
    except asyncio.CancelledError:
        pass
    finally:
        await runner.cleanup()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Webhook server stopped")
