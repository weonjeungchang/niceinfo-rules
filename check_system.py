"""시스템 환경 체크 스크립트"""

import os
import sys
from pathlib import Path


def check_python_version():
    """Python 버전 확인"""
    version = sys.version_info
    print(f"Python 버전: {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("  ❌ Python 3.8 이상이 필요합니다.")
        return False
    else:
        print("  ✓ Python 버전 확인")
        return True


def check_dependencies():
    """의존성 패키지 확인"""
    print("\n의존성 패키지 확인:")
    
    required_packages = [
        ('langchain', 'langchain'),
        ('openai', 'openai'),
        ('chromadb', 'chromadb'),
        ('streamlit', 'streamlit'),
        ('docx', 'python-docx'),
        ('openpyxl', 'openpyxl'),
        ('PyPDF2', 'PyPDF2'),
        ('dotenv', 'python-dotenv'),
    ]
    
    all_installed = True
    for module_name, package_name in required_packages:
        try:
            __import__(module_name)
            print(f"  ✓ {package_name}")
        except ImportError:
            print(f"  ❌ {package_name} (설치 필요)")
            all_installed = False
    
    return all_installed


def check_env_file():
    """환경 변수 파일 확인"""
    print("\n환경 설정 확인:")
    
    env_file = Path(".env")
    if env_file.exists():
        print("  ✓ .env 파일 존재")
        
        # API 키 확인
        from dotenv import load_dotenv
        load_dotenv()
        
        if os.getenv("OPENAI_API_KEY"):
            # API 키의 일부만 표시
            api_key = os.getenv("OPENAI_API_KEY")
            masked_key = api_key[:10] + "..." + api_key[-4:] if len(api_key) > 14 else "***"
            print(f"  ✓ OPENAI_API_KEY 설정됨 ({masked_key})")
            return True
        else:
            print("  ❌ OPENAI_API_KEY가 설정되지 않음")
            return False
    else:
        print("  ❌ .env 파일이 존재하지 않음")
        print("     env_template.txt를 참고하여 .env 파일을 생성하세요.")
        return False


def check_reference_folder():
    """reference 폴더 확인"""
    print("\n문서 폴더 확인:")
    
    ref_dir = Path("./reference")
    if not ref_dir.exists():
        print(f"  ❌ {ref_dir} 폴더가 존재하지 않음")
        return False
    
    print(f"  ✓ {ref_dir} 폴더 존재")
    
    # 문서 파일 수 확인
    doc_extensions = ['.doc', '.docx', '.xlsx', '.xls', '.pdf']
    doc_count = 0
    
    for ext in doc_extensions:
        count = len(list(ref_dir.rglob(f'*{ext}')))
        if count > 0:
            print(f"    - {ext}: {count}개")
            doc_count += count
    
    if doc_count == 0:
        print("  ⚠️  문서 파일이 없습니다.")
        return False
    else:
        print(f"  ✓ 총 {doc_count}개의 문서 파일")
        return True


def check_vector_db():
    """벡터 데이터베이스 확인"""
    print("\n벡터 데이터베이스 확인:")
    
    db_dir = Path("./chroma_db")
    if db_dir.exists():
        print(f"  ✓ {db_dir} 존재")
        
        # 파일 수 확인
        files = list(db_dir.rglob("*"))
        print(f"    - 파일 수: {len(files)}개")
        return True
    else:
        print(f"  ⚠️  {db_dir} 없음 (초기 설정 필요)")
        print("     setup_db.py를 실행하여 벡터 DB를 생성하세요.")
        return False


def check_windows_specific():
    """Windows 특정 확인"""
    if sys.platform == 'win32':
        print("\nWindows 환경 확인:")
        
        try:
            import win32com.client
            print("  ✓ win32com 설치됨 (.doc 파일 지원)")
            return True
        except ImportError:
            print("  ⚠️  win32com 미설치 (.doc 파일 처리 불가)")
            print("     pip install pywin32 실행 권장")
            return False
    return True


def main():
    """메인 함수"""
    print("=" * 60)
    print("NICE평가정보 내규 챗봇 - 시스템 환경 체크")
    print("=" * 60)
    print()
    
    checks = {
        "Python 버전": check_python_version(),
        "의존성 패키지": check_dependencies(),
        "환경 설정": check_env_file(),
        "문서 폴더": check_reference_folder(),
        "벡터 DB": check_vector_db(),
    }
    
    if sys.platform == 'win32':
        checks["Windows 환경"] = check_windows_specific()
    
    print()
    print("=" * 60)
    print("체크 결과 요약")
    print("=" * 60)
    
    all_passed = True
    for check_name, result in checks.items():
        status = "✓" if result else "❌"
        print(f"{status} {check_name}")
        if not result:
            all_passed = False
    
    print()
    
    if all_passed:
        print("✅ 모든 체크를 통과했습니다!")
        print("\n다음 단계:")
        
        if not Path("./chroma_db").exists():
            print("  1. python setup_db.py  # 벡터 DB 생성")
            print("  2. streamlit run app.py  # 챗봇 실행")
        else:
            print("  streamlit run app.py  # 챗봇 실행")
    else:
        print("⚠️  일부 체크를 통과하지 못했습니다.")
        print("\n해결 방법:")
        
        if not checks["의존성 패키지"]:
            print("  1. pip install -r requirements.txt")
        
        if not checks["환경 설정"]:
            print("  2. env_template.txt를 참고하여 .env 파일 생성")
            print("     OPENAI_API_KEY를 설정하세요")
        
        if not checks["문서 폴더"]:
            print("  3. ./reference 폴더에 내규 문서를 배치하세요")
        
        print("\n자세한 내용은 README.md를 참고하세요.")
    
    print()


if __name__ == "__main__":
    main()

