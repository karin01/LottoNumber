#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
라틴댄스 파티 서버 모니터링 스크립트
서버가 다운되면 자동으로 재시작합니다.
"""

import requests
import time
import subprocess
import os
import sys
from datetime import datetime

# 설정
SERVER_URL = "http://localhost:8000"
CHECK_INTERVAL = 60  # 60초마다 체크
MAX_RETRIES = 3
SERVER_SCRIPT = "python -m http.server 8000"
SERVER_DIR = "static"

def log_message(message):
    """로그 메시지 출력"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def check_server():
    """서버 상태 확인"""
    try:
        response = requests.get(SERVER_URL, timeout=10)
        if response.status_code == 200:
            return True
        else:
            log_message(f"서버 응답 오류: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        log_message(f"서버 연결 실패: {e}")
        return False

def start_server():
    """서버 시작"""
    try:
        log_message("서버 시작 중...")
        
        # 서버 디렉토리로 이동
        os.chdir(SERVER_DIR)
        
        # 서버 프로세스 시작
        process = subprocess.Popen(
            SERVER_SCRIPT.split(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        log_message(f"서버 프로세스 시작됨 (PID: {process.pid})")
        return process
    except Exception as e:
        log_message(f"서버 시작 실패: {e}")
        return None

def stop_server(process):
    """서버 중지"""
    if process:
        try:
            process.terminate()
            process.wait(timeout=5)
            log_message("서버 중지됨")
        except subprocess.TimeoutExpired:
            process.kill()
            log_message("서버 강제 종료됨")
        except Exception as e:
            log_message(f"서버 중지 오류: {e}")

def main():
    """메인 모니터링 루프"""
    log_message("라틴댄스 파티 서버 모니터링 시작")
    log_message(f"모니터링 URL: {SERVER_URL}")
    log_message(f"체크 간격: {CHECK_INTERVAL}초")
    
    server_process = None
    retry_count = 0
    
    try:
        while True:
            # 서버 상태 확인
            if check_server():
                log_message("✅ 서버 정상 동작 중")
                retry_count = 0  # 성공 시 재시도 카운트 리셋
            else:
                log_message("❌ 서버 오류 감지")
                retry_count += 1
                
                if retry_count >= MAX_RETRIES:
                    log_message(f"최대 재시도 횟수 도달 ({MAX_RETRIES}회)")
                    log_message("서버 재시작 중...")
                    
                    # 기존 서버 중지
                    stop_server(server_process)
                    
                    # 새 서버 시작
                    server_process = start_server()
                    retry_count = 0
                    
                    if server_process:
                        log_message("서버 재시작 완료")
                    else:
                        log_message("서버 재시작 실패")
                else:
                    log_message(f"재시도 {retry_count}/{MAX_RETRIES}")
            
            # 대기
            time.sleep(CHECK_INTERVAL)
            
    except KeyboardInterrupt:
        log_message("모니터링 중단됨 (Ctrl+C)")
        stop_server(server_process)
        log_message("모니터링 종료")
    except Exception as e:
        log_message(f"모니터링 오류: {e}")
        stop_server(server_process)

if __name__ == "__main__":
    main() 