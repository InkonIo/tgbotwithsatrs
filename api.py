"""
API для Mini App
Предоставляет список доступных подарков
"""

import os
import json
import logging
from aiohttp import web
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# Note: Keeping your database imports as they were
try:
    from database.models import get_session, Gift
except ImportError:
    # Fallback for demonstration if database module is not found in current environment
    logger = logging.getLogger(__name__)
    logger.warning("Database models not found, using mock data for demonstration")
    class Gift:
        pass

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


async def get_gifts(request):
    """GET /api/gifts - получить список доступных подарков"""
    try:
        # Check if database is available
        if 'get_session' in globals():
            session = get_session()
            gifts = session.query(Gift).filter(Gift.quantity > 0).all()
            gifts_data = [
                {
                    'id': gift.id,
                    'emoji': gift.emoji,
                    'name': gift.name,
                    'rarity': gift.rarity,
                    'quantity': gift.quantity
                }
                for gift in gifts
            ]
            session.close()
        else:
            # Mock data for testing
            gifts_data = [
                {"id": 1, "emoji": "💎", "name": "Legendary Gift", "rarity": "legendary", "quantity": 1},
                {"id": 2, "emoji": "⭐", "name": "Epic Gift", "rarity": "epic", "quantity": 3},
                {"id": 3, "emoji": "🎁", "name": "Rare Gift", "rarity": "rare", "quantity": 5},
                {"id": 4, "emoji": "🎀", "name": "Common Gift", "rarity": "common", "quantity": 10}
            ]
        
        logger.info(f"Returned {len(gifts_data)} available gifts")
        
        return web.json_response({
            'success': True,
            'gifts': gifts_data
        })
        
    except Exception as e:
        logger.error(f"Error getting gifts: {e}", exc_info=True)
        return web.json_response({
            'success': False,
            'error': str(e)
        }, status=500)


async def health_check(request):
    """GET / - проверка работоспособности API"""
    return web.json_response({
        'status': 'ok',
        'message': 'Gift API is running'
    })


@web.middleware
async def cors_middleware(request, handler):
    """CORS middleware для всех запросов с поддержкой ngrok bypass"""
    # Allowed headers - added ngrok-skip-browser-warning
    allow_headers = 'Content-Type, Authorization, ngrok-skip-browser-warning'
    
    # Handle preflight OPTIONS request
    if request.method == 'OPTIONS':
        return web.Response(
            status=200,
            headers={
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
                'Access-Control-Allow-Headers': allow_headers,
                'Access-Control-Max-Age': '3600'
            }
        )
    
    # Handle actual request
    try:
        response = await handler(request)
    except web.HTTPException as ex:
        response = ex
    except Exception as e:
        logger.error(f"Unhandled exception: {e}", exc_info=True)
        response = web.json_response({'success': False, 'error': str(e)}, status=500)
    
    # Add CORS headers to response
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = allow_headers
    
    return response


def create_app():
    """Создать web приложение"""
    app = web.Application(middlewares=[cors_middleware])
    
    # Роуты
    app.router.add_get('/', health_check)
    app.router.add_get('/api/gifts', get_gifts)
    # Options handler is now handled by middleware for all routes
    
    return app


if __name__ == '__main__':
    logger.info("🌐 Starting API server...")
    app = create_app()
    web.run_app(app, host='0.0.0.0', port=8080)
