"""챗봇 실행 헬퍼 스크립트"""

import os
import sys
import subprocess
from pathlib import Path


def check_prerequisites():
    """사전 요구사항 확인"""
    errors = []
    
    # Python 버전 확인
    if sys.version_info < (3, 8):
        errors.append("Python 3.8 이상이 필요합니다.")
    
    # .env 파일 확인
    if not Path(".env").exists():
        errors.append(".env 파일이 없습니다. env_template.txt를 참고하여 생성하세요.")
    
    # reference 폴더 확인
    if not Path("./reference").exists():
        errors.append("./reference 폴더가 없습니다.")
    
    # 패키지 확인
    try:
        import streamlit
    except ImportError:
        errors.append("필요한 패키지가 설치되지 않았습니다. 'pip install -r requirements.txt' 실행하세요.")
    
    return errors


def main():
    """메인 함수"""
    print("=" * 60)
    print("NICE평가정보 내규 챗봇")
    print("=" * 60)
    print()
    
    # 사전 확인
    print("시스템 확인 중...")
    errors = check_prerequisites()
    
    if errors:
        print("\n❌ 다음 문제를 해결해주세요:\n")
        for i, error in enumerate(errors, 1):
            print(f"  {i}. {error}")
        print()
        print("자세한 내용은 README.md를 참고하세요.")
        sys.exit(1)
    
    print("✓ 시스템 확인 완료")
    print()
    
    # Streamlit 실행
    print("챗봇을 시작합니다...")
    print("브라우저가 자동으로 열립니다.")
    print("종료하려면 Ctrl+C를 누르세요.")
    print()
    
    try:
        subprocess.run([sys.executable, "-m", "streamlit", "run", "app.py"])
    except KeyboardInterrupt:
        print("\n\n챗봇을 종료합니다.")
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

