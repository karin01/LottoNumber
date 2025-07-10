#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Share_Note 서비스 시작 스크립트
가상환경/파이썬 자동 설치 안내, venv 자동 생성, Ollama/Flask 서버 실행
"""

import os
import sys
import subprocess
import time
from pathlib import Path

def print_banner():
    print("=" * 50)
    print("    Share_Note 서비스 시작 스크립트")
    print("=" * 50)
    print()

def check_python():
    """파이썬 설치 여부 확인"""
    print("[0/4] 파이썬 설치 확인 중...")
    try:
        subprocess.run(["python", "--version"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("✓ 파이썬이 설치되어 있습니다.")
        return True
    except Exception:
        print("✗ 파이썬이 설치되어 있지 않습니다!")
        print("파이썬 공식 다운로드: https://www.python.org/downloads/")
        input("파이썬 설치 후 다시 실행해 주세요. 엔터를 누르면 종료됩니다...")
        return False

def create_venv_if_needed():
    """venv 폴더가 없으면 자동 생성"""
    print("[1/4] 가상환경(venv) 확인 중...")
    script_dir = Path(__file__).parent
    venv_dir = script_dir / "venv"
    if not venv_dir.exists():
        print("venv 폴더가 없습니다. 자동으로 생성합니다...")
        try:
            subprocess.run(["python", "-m", "venv", "venv"], check=True)
            print("✓ venv 생성 완료")
        except Exception as e:
            print(f"✗ venv 생성 실패: {e}")
            input("엔터를 누르면 종료됩니다...")
            return False
    else:
        print("✓ venv 폴더가 이미 있습니다.")
    return True

def activate_venv():
    """가상환경 활성화"""
    print("[2/4] 가상환경 활성화 중...")
    script_dir = Path(__file__).parent
    venv_activate = script_dir / "venv" / "Scripts" / "activate.bat"
    if venv_activate.exists():
        os.environ['VIRTUAL_ENV'] = str(script_dir / "venv")
        os.environ['PATH'] = str(script_dir / "venv" / "Scripts") + os.pathsep + os.environ['PATH']
        print("✓ 가상환경 활성화 완료")
        return True
    else:
        print("✗ 가상환경을 찾을 수 없습니다. venv 폴더가 있는지 확인하세요.")
        return False

def start_ollama():
    print("\n[3/4] Ollama 서버 시작 중...")
    try:
        subprocess.Popen(["ollama", "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(3)
        print("✓ Ollama 서버 시작 완료")
        return True
    except FileNotFoundError:
        print("✗ Ollama가 설치되어 있지 않습니다. https://ollama.com/download 에서 설치해 주세요.")
        input("엔터를 누르면 종료됩니다...")
        return False

def install_requirements():
    print("\n[4/4] 필요한 패키지 확인 중...")
    try:
        script_dir = Path(__file__).parent
        requirements_file = script_dir / "backend" / "requirements.txt"
        if requirements_file.exists():
            subprocess.run([sys.executable, "-m", "pip", "install", "-r", str(requirements_file)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("✓ 패키지 확인 완료")
        return True
    except Exception as e:
        print(f"✗ 패키지 설치 중 오류: {e}")
        input("엔터를 누르면 종료됩니다...")
        return False

def start_flask():
    print("\n[5/5] Flask 서버 시작 중...")
    print("✓ 모든 서비스가 시작되었습니다!")
    print()
    print("=" * 50)
    print("    서비스 정보")
    print("=" * 50)
    print("• 웹앱: http://localhost:5000")
    print("• Ollama API: http://localhost:11434")
    print()
    print("서비스를 종료하려면 Ctrl+C를 누르세요.")
    print("=" * 50)
    print()
    # PyInstaller 환경에서는 sys._MEIPASS에서 backend 경로를 찾음 (한글 주석)
    import sys
    if hasattr(sys, '_MEIPASS'):
        base_dir = Path(sys._MEIPASS)
    else:
        base_dir = Path(__file__).parent.resolve()
    backend_dir = base_dir / "backend"
    os.chdir(backend_dir)
    try:
        subprocess.run([sys.executable, "app.py"])
    except KeyboardInterrupt:
        print("\n서비스를 종료합니다...")
    except Exception as e:
        print(f"Flask 서버 시작 중 오류: {e}")

def main():
    print_banner()
    os.chdir(Path(__file__).parent)
    if not check_python():
        return
    if not create_venv_if_needed():
        return
    if not activate_venv():
        input("엔터를 누르면 종료됩니다...")
        return
    if not start_ollama():
        return
    if not install_requirements():
        return
    start_flask()

if __name__ == "__main__":
    main() 