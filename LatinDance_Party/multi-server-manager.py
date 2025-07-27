#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
멀티 서버 관리 스크립트
여러 개의 서버를 동시에 관리합니다.
"""

import subprocess
import time
import os
import sys
from datetime import datetime

# 서버 설정
SERVERS = {
    "latin-dance": {
        "name": "라틴댄스 파티",
        "port": 8000,
        "directory": "static",
        "command": "python -m http.server 8000"
    },
    "other-app": {
        "name": "다른 앱",
        "port": 8001,
        "directory": "other-app-folder",
        "command": "python -m http.server 8001"
    }
    # 추가 서버는 여기에 설정
}

# 실행 중인 서버 프로세스 저장
running_servers = {}

def log_message(message):
    """로그 메시지 출력"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def start_server(server_id):
    """특정 서버 시작"""
    if server_id not in SERVERS:
        log_message(f"알 수 없는 서버 ID: {server_id}")
        return False
    
    server_config = SERVERS[server_id]
    
    try:
        # 서버 디렉토리로 이동
        os.chdir(server_config["directory"])
        
        # 서버 프로세스 시작
        process = subprocess.Popen(
            server_config["command"].split(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        running_servers[server_id] = process
        log_message(f"✅ {server_config['name']} 서버 시작됨 (포트: {server_config['port']}, PID: {process.pid})")
        return True
        
    except Exception as e:
        log_message(f"❌ {server_config['name']} 서버 시작 실패: {e}")
        return False

def stop_server(server_id):
    """특정 서버 중지"""
    if server_id not in running_servers:
        log_message(f"실행 중인 서버가 없습니다: {server_id}")
        return False
    
    process = running_servers[server_id]
    server_config = SERVERS[server_id]
    
    try:
        process.terminate()
        process.wait(timeout=5)
        del running_servers[server_id]
        log_message(f"🛑 {server_config['name']} 서버 중지됨")
        return True
    except subprocess.TimeoutExpired:
        process.kill()
        del running_servers[server_id]
        log_message(f"🛑 {server_config['name']} 서버 강제 종료됨")
        return True
    except Exception as e:
        log_message(f"❌ {server_config['name']} 서버 중지 오류: {e}")
        return False

def start_all_servers():
    """모든 서버 시작"""
    log_message("🚀 모든 서버 시작 중...")
    
    for server_id in SERVERS:
        start_server(server_id)
        time.sleep(1)  # 서버 간 간격
    
    log_message("모든 서버 시작 완료")

def stop_all_servers():
    """모든 서버 중지"""
    log_message("🛑 모든 서버 중지 중...")
    
    for server_id in list(running_servers.keys()):
        stop_server(server_id)
        time.sleep(1)
    
    log_message("모든 서버 중지 완료")

def show_status():
    """서버 상태 표시"""
    print("\n" + "="*50)
    print("서버 상태")
    print("="*50)
    
    for server_id, server_config in SERVERS.items():
        status = "🟢 실행 중" if server_id in running_servers else "🔴 중지됨"
        print(f"{server_config['name']}: {status} (포트: {server_config['port']})")
    
    print("="*50)
    print("접속 주소:")
    for server_id, server_config in SERVERS.items():
        print(f"  {server_config['name']}: http://localhost:{server_config['port']}")
    print("="*50)

def show_menu():
    """메뉴 표시"""
    print("\n" + "="*50)
    print("멀티 서버 관리자")
    print("="*50)
    print("1. 모든 서버 시작")
    print("2. 모든 서버 중지")
    print("3. 서버 상태 확인")
    print("4. 특정 서버 시작")
    print("5. 특정 서버 중지")
    print("0. 종료")
    print("="*50)

def main():
    """메인 함수"""
    log_message("멀티 서버 관리자 시작")
    
    try:
        while True:
            show_menu()
            choice = input("선택하세요: ").strip()
            
            if choice == "1":
                start_all_servers()
            elif choice == "2":
                stop_all_servers()
            elif choice == "3":
                show_status()
            elif choice == "4":
                print("\n사용 가능한 서버:")
                for server_id, server_config in SERVERS.items():
                    print(f"  {server_id}: {server_config['name']}")
                server_id = input("시작할 서버 ID: ").strip()
                start_server(server_id)
            elif choice == "5":
                print("\n실행 중인 서버:")
                for server_id in running_servers:
                    print(f"  {server_id}: {SERVERS[server_id]['name']}")
                server_id = input("중지할 서버 ID: ").strip()
                stop_server(server_id)
            elif choice == "0":
                log_message("프로그램 종료")
                stop_all_servers()
                break
            else:
                print("잘못된 선택입니다.")
            
            input("\nEnter를 누르면 계속...")
            
    except KeyboardInterrupt:
        log_message("프로그램 중단됨 (Ctrl+C)")
        stop_all_servers()
    except Exception as e:
        log_message(f"오류 발생: {e}")
        stop_all_servers()

if __name__ == "__main__":
    main() 