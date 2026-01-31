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
from database.models import get_session, Gift

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


async def get_gifts(request):
    """GET /api/gifts - получить список доступных подарков"""
    try:
        session = get_session()
        
        # Получаем только подарки с quantity > 0
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


async def options_handler(request):
    """Handle OPTIONS requests for CORS preflight"""
    return web.Response(
        status=200,
        headers={
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization',
            'Access-Control-Max-Age': '3600'
        }
    )


@web.middleware
async def cors_middleware(request, handler):
    """CORS middleware для всех запросов"""
    # Handle preflight OPTIONS request
    if request.method == 'OPTIONS':
        return web.Response(
            status=200,
            headers={
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type, Authorization',
                'Access-Control-Max-Age': '3600'
            }
        )
    
    # Handle actual request
    response = await handler(request)
    
    # Add CORS headers to response
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    
    return response


def create_app():
    """Создать web приложение"""
    app = web.Application(middlewares=[cors_middleware])
    
    # Роуты
    app.router.add_get('/', health_check)
    app.router.add_get('/api/gifts', get_gifts)
    app.router.add_options('/api/gifts', options_handler)
    
    return app


if __name__ == '__main__':
    logger.info("🌐 Starting API server...")
    app = create_app()
    web.run_app(app, host='0.0.0.0', port=8080)