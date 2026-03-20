#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
PyInstaller를 사용하여 Seoul Reservation Bot을 실행파일(.exe)로 변환하는 스크립트
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

# 한글 인코딩 처리
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 프로젝트 경로
PROJECT_DIR = Path(__file__).parent
DIST_DIR = PROJECT_DIR / 'dist'
BUILD_DIR = PROJECT_DIR / 'build'
TEMPLATES_DIR = PROJECT_DIR / 'templates'
STATIC_DIR = PROJECT_DIR / 'static'

def clean_build_artifacts():
    """이전 빌드 산물 정리"""
    print("이전 빌드 산물을 정리합니다...")
    
    for directory in [BUILD_DIR, PROJECT_DIR / 'build', PROJECT_DIR / '__pycache__']:
        if directory.exists():
            shutil.rmtree(directory)
            print(f"  [OK] {directory} 제거됨")
    
    # .spec 파일 제거
    spec_file = PROJECT_DIR / 'Seoul_Reservation_Bot.spec'
    if spec_file.exists():
        spec_file.unlink()
        print(f"  [OK] {spec_file.name} 제거됨")

def build_exe():
    """PyInstaller를 사용하여 실행파일 생성"""
    print("\n실행파일을 생성합니다...")
    
    # PyInstaller 명령어 구성
    cmd = [
        'pyinstaller',
        '--onefile',
        '--windowed',
        '--name', 'Seoul_Reservation_Bot',
        '--icon', 'NONE',
        '--distpath', str(DIST_DIR),
        '--workpath', str(BUILD_DIR),
        '--add-data', f'{TEMPLATES_DIR}{os.pathsep}templates',
        '--add-data', f'{STATIC_DIR}{os.pathsep}static',
        '--collect-all', 'flask',
        '--collect-all', 'flask_cors',
        'app.py'
    ]
    
    try:
        result = subprocess.run(cmd, cwd=PROJECT_DIR, check=True)
        print("  [OK] 실행파일 생성 성공!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"  [ERROR] 실행파일 생성 실패: {e}")
        return False

def copy_env_file():
    """환경 변수 파일 복사"""
    print("\n환경 설정 파일을 복사합니다...")
    
    env_file = PROJECT_DIR / '.env'
    if env_file.exists():
        dist_env = DIST_DIR / '.env'
        shutil.copy(env_file, dist_env)
        print(f"  [OK] .env 파일이 dist 디렉토리에 복사되었습니다")
    else:
        print(f"  [WARNING] .env 파일을 찾을 수 없습니다. dist 폴더에 .env 파일을 복사해주세요.")

def create_batch_launcher():
    """배치 파일 생성 (배포 패키지용)"""
    print("\n배포용 배치 파일을 생성합니다...")
    
    batch_content = """@echo off
chcp 65001 > nul
cls
echo.
echo ======================================
echo 서울시 예약 알림 봇 (Seoul Reservation Bot)
echo ======================================
echo.
echo 프로그램을 시작합니다...
echo 브라우저가 자동으로 열립니다.
echo 열리지 않으면 http://localhost:5000 으로 접속하세요.
echo.
echo (종료하려면 이 창을 닫으면 됩니다)
echo.

Seoul_Reservation_Bot.exe
"""
    
    batch_file = DIST_DIR / 'run.bat'
    with open(batch_file, 'w', encoding='utf-8') as f:
        f.write(batch_content)
    
    print(f"  [OK] run.bat 파일 생성됨")

def create_readme():
    """배포용 README 생성"""
    print("\n배포용 README를 생성합니다...")
    
    readme_content = """# 서울시 예약 알림 봇 (Seoul Reservation Bot)

## 실행 방법

### 1. 첫 번째 실행 (권장)
- run.bat 파일을 더블클릭하면 프로그램이 자동으로 시작됩니다.

### 2. 직접 실행
- Seoul_Reservation_Bot.exe 파일을 더블클릭하면 프로그램이 시작됩니다.

## 필수 설정

프로그램 실행 전에 .env 파일에 다음 정보를 입력해주세요:

TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
SEOUL_API_KEY=your_seoul_api_key_here

## 사용 방법

1. 프로그램 실행: run.bat 또는 .exe 파일 더블클릭
2. 브라우저 접속: 자동으로 http://localhost:5000 페이지가 열립니다
3. 설정 조정: 가져올 공고 수, 알림 전송 수 설정
4. 실행: "1회 전송 실행" 버튼 클릭
5. 결과 확인: 실행 결과 및 통계 확인

## 폴더 구조

Seoul_Reservation_Bot/
- Seoul_Reservation_Bot.exe    (메인 실행파일)
- run.bat                      (배치 실행 파일 - 권장)
- .env                         (환경 설정 파일 - 필수)
- README.txt                   (이 파일)

## 문제 해결

### 프로그램이 실행되지 않을 때
1. .env 파일이 같은 폴더에 있는지 확인하세요
2. 텔레그램 봇 토큰과 채팅 ID가 올바른지 확인하세요
3. 5000번 포트가 다른 프로그램에 의해 사용되고 있지 않은지 확인하세요

### 네트워크 연결 오류
- 인터넷 연결을 확인하세요
- 방화벽 설정을 확인하세요

### 텔레그램 메시지 미수신
1. 봇 토큰이 올바른지 확인하세요
2. 채팅 ID가 올바른지 확인하세요
3. 봇이 시작 메시지를 받았는지 확인하세요 (/start 명령어)

## 기타 정보

- 개발 언어: Python 3.11
- 웹 프레임워크: Flask
- 메시징 플랫폼: Telegram
- 데이터베이스: SQLite

---

주의: 이 프로그램은 서울시 공공데이터를 사용합니다.
과도한 API 호출을 피하고 적절한 간격으로 사용해주세요.
"""
    
    readme_file = DIST_DIR / 'README.txt'
    with open(readme_file, 'w', encoding='utf-8') as f:
        f.write(readme_content)
    
    print(f"  [OK] README.txt 파일 생성됨")

def main():
    """메인 빌드 함수"""
    print("=" * 50)
    print("Seoul Reservation Bot 실행파일 생성 시작")
    print("=" * 50)
    
    # 1. 이전 빌드 산물 정리
    clean_build_artifacts()
    
    # 2. 실행파일 생성
    if not build_exe():
        print("\n실행파일 생성에 실패했습니다.")
        sys.exit(1)
    
    # 3. 배포 디렉토리 확인
    if not DIST_DIR.exists():
        print(f"[ERROR] dist 디렉토리를 찾을 수 없습니다.")
        sys.exit(1)
    
    # 4. 환경 변수 파일 복사
    copy_env_file()
    
    # 5. 배치 파일 생성
    create_batch_launcher()
    
    # 6. README 생성
    create_readme()
    
    # 완료
    print("\n" + "=" * 50)
    print("[OK] 실행파일 생성 완료!")
    print("=" * 50)
    print(f"\n생성된 파일 위치: {DIST_DIR}")
    print(f"\n다음 파일들이 생성되었습니다:")
    print(f"  1. Seoul_Reservation_Bot.exe (메인 실행파일)")
    print(f"  2. run.bat (배치 실행 파일 - 권장)")
    print(f"  3. .env (환경 설정 파일)")
    print(f"  4. README.txt (사용 설명서)")
    print(f"\n배포를 위해 dist 폴더 전체를 압축하면 됩니다.")
    print(f"\n실행 방법: dist 폴더 내의 run.bat 파일을 더블클릭하세요.")

if __name__ == '__main__':
    main()
