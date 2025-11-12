"""벡터 데이터베이스 초기 설정 스크립트"""

import os
import sys
from pathlib import Path
import logging

from dotenv import load_dotenv

from src.document_loader import DocumentLoader
from src.vector_store import VectorStoreManager

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """메인 함수"""
    print("=" * 60)
    print("NICE평가정보 내규 챗봇 - 데이터베이스 설정")
    print("=" * 60)
    print()
    
    # 환경 변수 로드
    load_dotenv()
    
    # API 키 확인
    if not os.getenv("OPENAI_API_KEY"):
        logger.error("❌ OPENAI_API_KEY가 설정되지 않았습니다.")
        logger.error("   .env 파일을 생성하고 API 키를 설정하세요.")
        logger.error("   자세한 내용은 README.md를 참고하세요.")
        sys.exit(1)
    
    logger.info("✓ OpenAI API 키 확인 완료")
    
    # reference 폴더 확인
    reference_dir = Path("./reference")
    if not reference_dir.exists():
        logger.error(f"❌ {reference_dir} 폴더가 존재하지 않습니다.")
        sys.exit(1)
    
    logger.info(f"✓ 문서 폴더 확인 완료: {reference_dir}")
    
    # 기존 벡터 스토어 확인
    chroma_db_dir = Path("./chroma_db")
    if chroma_db_dir.exists():
        response = input("\n⚠️  기존 벡터 데이터베이스가 존재합니다. 삭제하고 재생성하시겠습니까? (y/N): ")
        if response.lower() != 'y':
            logger.info("작업이 취소되었습니다.")
            sys.exit(0)
        
        logger.info("기존 벡터 데이터베이스를 삭제합니다...")
        import shutil
        shutil.rmtree(chroma_db_dir)
        logger.info("✓ 삭제 완료")
    
    print()
    print("-" * 60)
    print("1단계: 문서 로딩")
    print("-" * 60)
    
    try:
        # 문서 로더 초기화
        loader = DocumentLoader(str(reference_dir))
        
        # 문서 로드
        logger.info("문서를 로드하는 중...")
        documents = loader.load_documents()
        
        if not documents:
            logger.error("❌ 로드된 문서가 없습니다.")
            sys.exit(1)
        
        logger.info(f"✓ 총 {len(documents)}개의 문서가 로드되었습니다.")
        
        # 카테고리별 통계
        categories = {}
        for doc in documents:
            category = doc.metadata.get('category', '기타')
            categories[category] = categories.get(category, 0) + 1
        
        print("\n카테고리별 문서 수:")
        for category, count in sorted(categories.items()):
            print(f"  - {category}: {count}개")
        
    except Exception as e:
        logger.error(f"❌ 문서 로딩 중 오류 발생: {e}")
        sys.exit(1)
    
    print()
    print("-" * 60)
    print("2단계: 벡터 데이터베이스 생성")
    print("-" * 60)
    
    try:
        # 벡터 스토어 관리자 초기화
        vs_manager = VectorStoreManager(
            persist_directory="./chroma_db",
            chunk_size=1000,
            chunk_overlap_percent=4.0  # 4% 오버랩 (40자)
        )
        
        # 벡터 스토어 생성
        logger.info("벡터 임베딩을 생성하고 데이터베이스에 저장하는 중...")
        logger.info("청크 설정: size=1000, overlap=40 (4%)")
        logger.info("(문서 크기에 따라 5-10분 정도 걸릴 수 있습니다)")
        
        vectorstore = vs_manager.create_vectorstore(documents, force_recreate=True)
        
        logger.info("✓ 벡터 데이터베이스 생성 완료!")
        
    except Exception as e:
        logger.error(f"❌ 벡터 데이터베이스 생성 중 오류 발생: {e}")
        sys.exit(1)
    
    print()
    print("-" * 60)
    print("3단계: 테스트 검색")
    print("-" * 60)
    
    try:
        # 테스트 검색
        test_queries = [
            "직원 복무 규정",
            "연차 휴가",
            "급여 지급"
        ]
        
        for query in test_queries:
            logger.info(f"\n테스트 쿼리: '{query}'")
            results = vs_manager.similarity_search(query, k=2)
            
            if results:
                for i, (doc, score) in enumerate(results, 1):
                    print(f"  결과 {i}: {doc.metadata.get('filename', 'Unknown')} "
                          f"(유사도: {1-score:.4f})")
            else:
                print("  결과 없음")
        
        logger.info("\n✓ 테스트 검색 완료!")
        
    except Exception as e:
        logger.warning(f"⚠️  테스트 검색 중 오류 발생: {e}")
    
    print()
    print("=" * 60)
    print("✅ 설정이 완료되었습니다!")
    print("=" * 60)
    print()
    print("이제 다음 명령어로 챗봇을 실행할 수 있습니다:")
    print("  streamlit run app.py")
    print()


if __name__ == "__main__":
    main()

