import hashlib
import json
from typing import Optional, Callable, Any
from functools import wraps
from config.redis_config import get_redis
from util.log.log import Log

logger = Log.get_logger()
redis_client = get_redis()


class AICache:
    """AI 응답 캐싱을 위한 유틸리티 클래스"""
    
    DEFAULT_TTL = 86400  # 24시간
    
    @staticmethod
    def generate_cache_key(data_str: str, endpoint_name: str) -> str:
        """
        데이터 해시값과 엔드포인트명으로 캐시 키 생성
        
        Args:
            data_str: 사용자 데이터 문자열
            endpoint_name: API 엔드포인트명
            
        Returns:
            캐시 키 (예: "ai_cache:future-assets:a1b2c3d4...")
        """
        data_hash = hashlib.md5(data_str.encode('utf-8')).hexdigest()
        return f"ai_cache:{endpoint_name}:{data_hash}"
    
    @staticmethod
    def get_cached_response(cache_key: str) -> Optional[str]:
        """
        Redis에서 캐시된 응답 조회
        
        Args:
            cache_key: 캐시 키
            
        Returns:
            캐시된 응답 또는 None
        """
        try:
            cached_data = redis_client.get(cache_key)
            if cached_data:
                logger.info(f"✅ Cache HIT: {cache_key}")
                return cached_data
            else:
                logger.info(f"❌ Cache MISS: {cache_key}")
                return None
        except Exception as e:
            logger.error(f"Cache read error: {e}")
            return None
    
    @staticmethod
    def set_cached_response(cache_key: str, response: str, ttl: int = DEFAULT_TTL) -> bool:
        """
        Redis에 응답 캐싱
        
        Args:
            cache_key: 캐시 키
            response: AI 응답
            ttl: 캐시 유효 시간 (초)
            
        Returns:
            성공 여부
        """
        try:
            redis_client.setex(cache_key, ttl, response)
            logger.info(f"💾 Cache STORED: {cache_key} (TTL: {ttl}s)")
            return True
        except Exception as e:
            logger.error(f"Cache write error: {e}")
            return False
    
    @staticmethod
    def invalidate_cache(cache_key: str) -> bool:
        """
        특정 캐시 무효화
        
        Args:
            cache_key: 캐시 키
            
        Returns:
            성공 여부
        """
        try:
            result = redis_client.delete(cache_key)
            logger.info(f"🗑️ Cache INVALIDATED: {cache_key}")
            return result > 0
        except Exception as e:
            logger.error(f"Cache invalidation error: {e}")
            return False
    
    @staticmethod
    def invalidate_user_cache(session_id: str) -> int:
        """
        특정 사용자의 모든 캐시 무효화
        
        Args:
            session_id: 세션 ID
            
        Returns:
            삭제된 캐시 개수
        """
        try:
            # ai_cache:* 패턴의 모든 키 찾기
            pattern = f"ai_cache:*"
            keys = redis_client.keys(pattern)
            
            if keys:
                deleted = redis_client.delete(*keys)
                logger.info(f"🗑️ User cache INVALIDATED: {deleted} keys deleted")
                return deleted
            return 0
        except Exception as e:
            logger.error(f"User cache invalidation error: {e}")
            return 0
    
    @staticmethod
    def get_cache_stats() -> dict:
        """
        캐시 통계 조회
        
        Returns:
            캐시 통계 딕셔너리
        """
        try:
            pattern = "ai_cache:*"
            keys = redis_client.keys(pattern)
            
            stats = {
                "total_cached_items": len(keys),
                "cache_keys": keys[:10] if keys else [],  # 처음 10개만
                "redis_info": redis_client.info("memory")
            }
            return stats
        except Exception as e:
            logger.error(f"Cache stats error: {e}")
            return {}


def with_cache(endpoint_name: str, ttl: int = AICache.DEFAULT_TTL):
    """
    AI 응답 캐싱 데코레이터
    
    사용 예시:
    @with_cache(endpoint_name="future-assets", ttl=86400)
    async def some_ai_function(data_str: str):
        return await call_gpt(data_str)
    
    Args:
        endpoint_name: 엔드포인트명
        ttl: 캐시 유효 시간 (초)
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(data_str: str, *args, **kwargs) -> str:
            # 캐시 키 생성
            cache_key = AICache.generate_cache_key(data_str, endpoint_name)
            
            # 캐시 조회
            cached_response = AICache.get_cached_response(cache_key)
            if cached_response:
                return cached_response
            
            # 캐시 미스 - 원본 함수 실행
            response = await func(data_str, *args, **kwargs)
            
            # 캐시 저장
            AICache.set_cached_response(cache_key, response, ttl)
            
            return response
        return wrapper
    return decorator
