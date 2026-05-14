#!/usr/bin/env python3
"""
텔레그램 전송 문제를 진단하는 테스트 스크립트
"""
import asyncio
import logging
from notifier import Notifier

# 로깅 설정
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", 
    level=logging.DEBUG
)
logger = logging.getLogger(__name__)


async def test_telegram():
    """텔레그램 연결 및 메시지 전송 테스트"""
    logger.info("=" * 60)
    logger.info("텔레그램 전송 테스트 시작")
    logger.info("=" * 60)
    
    try:
        # 1. Notifier 객체 생성
        logger.info("\n[1단계] Notifier 객체 생성 중...")
        notifier = Notifier()
        logger.info("✓ Notifier 객체 생성 성공")
        
        # 2. 테스트 메시지 생성
        logger.info("\n[2단계] 테스트 메시지 생성 중...")
        test_message = "🧪 <b>텔레그램 전송 테스트</b>\n이 메시지가 수신되면 정상 작동합니다."
        logger.info(f"메시지: {test_message}")
        
        # 3. 메시지 전송
        logger.info("\n[3단계] 메시지 전송 중...")
        result = await notifier.send_message(test_message)
        
        if result:
            logger.info("\n" + "=" * 60)
            logger.info("✓ 테스트 PASSED - 텔레그램 연결 정상")
            logger.info("=" * 60)
        else:
            logger.error("\n" + "=" * 60)
            logger.error("✗ 테스트 FAILED - 메시지 전송 실패")
            logger.error("=" * 60)
            
    except ValueError as e:
        logger.error("\n" + "=" * 60)
        logger.error(f"❌ 설정 오류: {e}")
        logger.error("원인: .env 파일의 TELEGRAM_BOT_TOKEN 또는 TELEGRAM_CHAT_ID가 설정되지 않음")
        logger.error("=" * 60)
    except Exception as e:
        logger.error("\n" + "=" * 60)
        logger.error(f"❌ 예기치 않은 오류: {type(e).__name__} - {e}")
        logger.error("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_telegram())
