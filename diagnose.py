#!/usr/bin/env python3
"""
전체 실행 흐름을 로깅하는 진단 스크립트
7개의 공고를 받아서 텔레그램 전송까지 진행하면서 각 단계를 로깅합니다.
"""
import asyncio
import logging
from scraper import Scraper
from storage import Storage
from notifier import Notifier

# 상세 로깅 설정
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", 
    level=logging.DEBUG,
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('debug.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)


async def diagnose_full_flow(fetch_limit=500, notify_limit=30):
    """전체 실행 흐름을 진단"""
    logger.info("=" * 80)
    logger.info("📊 전체 실행 흐름 진단 시작")
    logger.info("=" * 80)
    
    try:
        # 1단계: Scraper 테스트
        logger.info("\n[1단계] 서울시 API 데이터 수집")
        logger.info("-" * 80)
        scraper = Scraper()
        reservations = scraper.fetch_new_reservations(fetch_limit=fetch_limit)
        logger.info(f"✓ 수집 완료: {len(reservations)}개의 공고")
        
        if not reservations:
            logger.error("✗ 수집된 공고가 없습니다!")
            return
        
        # 첫 3개 샘플 출력
        for idx, res in enumerate(reservations[:3], 1):
            logger.debug(f"  샘플 {idx}: {res.get('svc_name', 'N/A')}")
        
        # 2단계: Storage 테스트
        logger.info("\n[2단계] 데이터베이스 상태 확인")
        logger.info("-" * 80)
        storage = Storage()
        
        # 이미 본 공고 확인
        already_seen = 0
        new_count = 0
        for res in reservations:
            if storage.is_seen(res['svc_id']):
                already_seen += 1
            else:
                new_count += 1
        
        logger.info(f"✓ 이미 본 공고: {already_seen}개")
        logger.info(f"✓ 새로운 공고: {new_count}개")
        
        if new_count == 0:
            logger.warning("⚠️ 새로운 공고가 없습니다. (모두 이미 본 공고)")
            return
        
        # 3단계: Notifier 테스트
        logger.info("\n[3단계] 텔레그램 연결 테스트")
        logger.info("-" * 80)
        notifier = Notifier()
        logger.info("✓ 텔레그램 봇 객체 생성 완료")
        
        # 4단계: 메시지 포맷팅 및 전송
        logger.info("\n[4단계] 메시지 포맷팅 및 전송")
        logger.info("-" * 80)
        
        sent_count = 0
        failed_count = 0
        
        # notify_limit 개수만큼만 처리
        reservations_to_send = reservations[-notify_limit:] if len(reservations) > notify_limit else reservations
        
        for idx, reservation in enumerate(reservations_to_send, 1):
            svc_id = reservation["svc_id"]
            svc_name = reservation.get("svc_name", "알 수 없음")
            
            if not storage.is_seen(svc_id):
                logger.info(f"\n  [{idx}] 처리 중: {svc_name}")
                
                try:
                    # 메시지 포맷팅
                    message = notifier.format_message(reservation)
                    logger.debug(f"  포맷팅 완료")
                    
                    # 메시지 전송
                    if await notifier.send_message(message):
                        storage.add_seen(svc_id)
                        sent_count += 1
                        logger.info(f"  ✓ 전송 성공")
                        await asyncio.sleep(1)  # Rate limiting
                    else:
                        failed_count += 1
                        logger.error(f"  ✗ 전송 실패")
                        
                except Exception as e:
                    failed_count += 1
                    logger.error(f"  ✗ 오류: {type(e).__name__} - {e}")
            else:
                logger.debug(f"  [{idx}] 스킵 (이미 본 공고): {svc_name}")
        
        # 최종 결과
        logger.info("\n" + "=" * 80)
        logger.info("📈 진단 완료 - 최종 결과")
        logger.info("=" * 80)
        logger.info(f"총 공고 수집: {len(reservations)}")
        logger.info(f"새로운 공고: {new_count}")
        logger.info(f"전송 성공: {sent_count}")
        logger.info(f"전송 실패: {failed_count}")
        
        if sent_count > 0:
            logger.info("✓ 정상 작동 - 텔레그램으로 메시지가 전송되었습니다!")
        elif failed_count > 0:
            logger.error("✗ 문제 발생 - 텔레그램 전송 실패")
            logger.error("위의 로그를 확인하여 원인을 파악하세요.")
        else:
            logger.warning("⚠️ 새로운 공고가 없어 전송할 항목이 없습니다.")
        
        logger.info("=" * 80)
        logger.info("📝 상세 로그는 debug.log 파일에 저장되었습니다.")
        
    except Exception as e:
        logger.error("=" * 80)
        logger.error(f"❌ 진단 중 오류 발생: {type(e).__name__} - {e}")
        logger.error("=" * 80)


if __name__ == "__main__":
    import sys
    
    fetch_limit = int(sys.argv[1]) if len(sys.argv) > 1 else 500
    notify_limit = int(sys.argv[2]) if len(sys.argv) > 2 else 30
    
    asyncio.run(diagnose_full_flow(fetch_limit=fetch_limit, notify_limit=notify_limit))
