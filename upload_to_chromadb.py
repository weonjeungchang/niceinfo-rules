"""ChromaDB Cloud에 문서를 한 번만 업로드하는 스크립트"""

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
    print("=" * 70)
    print("ChromaDB Cloud 문서 업로드 스크립트")
    print("=" * 70)
    print()
    
    # 환경 변수 로드
    load_dotenv()
    
    # API 키 확인
    openai_key = os.getenv("OPENAI_API_KEY")
    chroma_key = os.getenv("CHROMA_API_KEY")
    chroma_tenant = os.getenv("CHROMA_TENANT")
    chroma_database = os.getenv("CHROMA_DATABASE")
    chroma_collection = os.getenv("CHROMA_COLLECTION", "niceinfo-rules")
    
    if not openai_key:
        logger.error("❌ OPENAI_API_KEY가 설정되지 않았습니다.")
        logger.error("   .env 파일을 확인하세요.")
        sys.exit(1)
    
    if not chroma_key:
        logger.error("❌ CHROMA_API_KEY가 설정되지 않았습니다.")
        logger.error("   ChromaDB Cloud 사용을 위해 .env 파일에 설정하세요.")
        sys.exit(1)
    
    logger.info("✓ API 키 확인 완료")
    logger.info(f"✓ ChromaDB Cloud 설정:")
    logger.info(f"   - Tenant: {chroma_tenant}")
    logger.info(f"   - Database: {chroma_database}")
    logger.info(f"   - Collection: {chroma_collection}")
    
    # reference 폴더 확인
    reference_dir = Path("./reference")
    if not reference_dir.exists():
        logger.error(f"❌ {reference_dir} 폴더가 존재하지 않습니다.")
        sys.exit(1)
    
    logger.info(f"✓ 문서 폴더 확인 완료: {reference_dir}")
    print()
    
    # 사용자 확인
    print("[주의] 이 작업은 ChromaDB Cloud에 문서를 업로드합니다.")
    print(f"   컬렉션: {chroma_collection}")
    print()
    response = input("계속하시겠습니까? (y/N): ")
    if response.lower() != 'y':
        logger.info("작업이 취소되었습니다.")
        sys.exit(0)
    
    print()
    print("-" * 70)
    print("1단계: 문서 로딩")
    print("-" * 70)
    
    try:
        # 문서 로더 초기화
        loader = DocumentLoader(str(reference_dir))
        
        # 문서 로드 (ZIP 파일 자동 제외)
        logger.info("문서를 로드하는 중... (ZIP 파일은 자동으로 제외됩니다)")
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
        
        print("\n[통계] 카테고리별 문서 수:")
        for category, count in sorted(categories.items()):
            print(f"  - {category}: {count}개")
        
    except Exception as e:
        logger.error(f"❌ 문서 로딩 중 오류 발생: {e}")
        sys.exit(1)
    
    print()
    print("-" * 70)
    print("2단계: ChromaDB Cloud에 업로드")
    print("-" * 70)
    
    try:
        # 벡터 스토어 관리자 초기화
        logger.info("ChromaDB Cloud 연결 중...")
        vs_manager = VectorStoreManager(
            chunk_size=1500,  # 더 큰 청크로 변경 (1000 -> 1500)
            chunk_overlap_percent=10.0,  # 더 많은 오버랩 (4% -> 10%)
            use_cloud=True,
            cloud_api_key=chroma_key,
            cloud_tenant=chroma_tenant,
            cloud_database=chroma_database,
            collection_name=chroma_collection
        )
        
        logger.info("✓ ChromaDB Cloud 연결 완료")
        print()
        
        # 기존 컬렉션 확인
        print("⚠️  기존 컬렉션이 있는 경우 덮어쓰게 됩니다.")
        response = input("기존 컬렉션을 삭제하고 새로 생성하시겠습니까? (y/N): ")
        
        force_recreate = response.lower() == 'y'
        
        if force_recreate:
            logger.info("기존 컬렉션을 삭제합니다...")
            try:
                vs_manager.delete_vectorstore()
            except Exception as e:
                logger.warning(f"컬렉션 삭제 시 오류 (무시됨): {e}")
        
        print()
        # 벡터 스토어 생성 및 업로드
        logger.info("벡터 임베딩 생성 및 ChromaDB Cloud에 업로드 중...")
        logger.info("📝 청크 설정: 크기=1500자, 오버랩=150자 (10%)")
        logger.info("⏳ 이 작업은 문서 크기에 따라 수 분이 걸릴 수 있습니다...")
        print()
        
        vectorstore = vs_manager.create_vectorstore(
            documents, 
            force_recreate=force_recreate
        )
        
        logger.info("✓ ChromaDB Cloud에 업로드 완료!")
        
    except Exception as e:
        logger.error(f"❌ ChromaDB Cloud 업로드 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    print()
    print("-" * 70)
    print("3단계: 업로드 검증")
    print("-" * 70)
    
    try:
        # 테스트 검색
        test_queries = [
            "직원 복무 규정",
            "연차 휴가",
            "급여 지급"
        ]
        
        for query in test_queries:
            logger.info(f"\n🔍 테스트 쿼리: '{query}'")
            results = vs_manager.similarity_search(query, k=2)
            
            if results:
                for i, (doc, score) in enumerate(results, 1):
                    print(f"  ✓ 결과 {i}: {doc.metadata.get('filename', 'Unknown')} "
                          f"(유사도: {1-score:.4f})")
            else:
                print("  ⚠️  결과 없음")
        
        logger.info("\n✓ 업로드 검증 완료!")
        
    except Exception as e:
        logger.warning(f"⚠️  검증 중 오류 발생: {e}")
    
    print()
    print("=" * 70)
    print("✅ 모든 작업이 완료되었습니다!")
    print("=" * 70)
    print()
    print("📌 다음 단계:")
    print("   1. 챗봇을 실행하세요: streamlit run app.py")
    print("   2. 챗봇은 ChromaDB Cloud의 데이터를 자동으로 로드합니다")
    print()
    print("⚠️  주의: 문서가 변경된 경우에만 이 스크립트를 다시 실행하세요")
    print()


if __name__ == "__main__":
    main()

