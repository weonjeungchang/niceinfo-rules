"""벡터 스토어 관리 모듈"""

import os
from typing import List, Optional
import logging
import chromadb

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VectorStoreManager:
    """벡터 스토어 관리 클래스 (로컬 및 ChromaDB Cloud 지원)"""
    
    def __init__(
        self,
        persist_directory: str = "./chroma_db",
        embedding_model: str = "text-embedding-3-small",
        chunk_size: int = 1000,
        chunk_overlap_percent: float = 4.0,
        use_cloud: bool = False,
        cloud_api_key: Optional[str] = None,
        cloud_tenant: Optional[str] = None,
        cloud_database: Optional[str] = None,
        collection_name: str = "niceinfo-rules"
    ):
        """
        Args:
            persist_directory: ChromaDB 저장 디렉토리 (로컬 사용 시)
            embedding_model: OpenAI 임베딩 모델
            chunk_size: 텍스트 청크 크기
            chunk_overlap_percent: 청크 간 중복 비율 (%) - 기본 4%
            use_cloud: ChromaDB Cloud 사용 여부
            cloud_api_key: ChromaDB Cloud API 키
            cloud_tenant: ChromaDB Cloud Tenant ID
            cloud_database: ChromaDB Cloud Database 이름
            collection_name: 컬렉션 이름
        """
        self.persist_directory = persist_directory
        self.embedding_model = embedding_model
        self.chunk_size = chunk_size
        self.chunk_overlap_percent = chunk_overlap_percent
        # 4% 오버랩 계산
        self.chunk_overlap = int(chunk_size * (chunk_overlap_percent / 100))
        self.use_cloud = use_cloud
        self.cloud_api_key = cloud_api_key
        self.cloud_tenant = cloud_tenant
        self.cloud_database = cloud_database
        self.collection_name = collection_name
        
        # OpenAI 임베딩 초기화
        self.embeddings = OpenAIEmbeddings(model=embedding_model)
        
        # 텍스트 스플리터 초기화 (4% 오버랩)
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", "。", ".", " ", ""]
        )
        
        logger.info(f"청크 설정: size={chunk_size}, overlap={self.chunk_overlap} ({chunk_overlap_percent}%)")
        
        # ChromaDB 클라이언트 초기화
        self.client = None
        if self.use_cloud:
            if not all([cloud_api_key, cloud_tenant, cloud_database]):
                raise ValueError("ChromaDB Cloud 사용 시 api_key, tenant, database가 필요합니다.")
            
            logger.info("ChromaDB Cloud 클라이언트를 초기화합니다...")
            self.client = chromadb.CloudClient(
                api_key=cloud_api_key,
                tenant=cloud_tenant,
                database=cloud_database
            )
            logger.info(f"ChromaDB Cloud 연결 완료 (Tenant: {cloud_tenant}, DB: {cloud_database})")
        
        self.vectorstore: Optional[Chroma] = None
    
    def create_vectorstore(self, documents: List[Document], force_recreate: bool = False) -> Chroma:
        """
        문서로부터 벡터 스토어를 생성합니다.
        
        Args:
            documents: 문서 리스트
            force_recreate: 기존 벡터 스토어를 강제로 재생성할지 여부
        
        Returns:
            Chroma 벡터 스토어
        """
        # Cloud가 아니고 기존 벡터 스토어가 있고 재생성하지 않는 경우
        if not self.use_cloud and not force_recreate and os.path.exists(self.persist_directory):
            logger.info("기존 벡터 스토어를 로드합니다...")
            return self.load_vectorstore()
        
        logger.info(f"총 {len(documents)}개의 문서를 처리합니다...")
        
        # 문서를 청크로 분할
        logger.info("문서를 청크로 분할하는 중...")
        chunks = self.text_splitter.split_documents(documents)
        logger.info(f"총 {len(chunks)}개의 청크가 생성되었습니다.")
        
        # 벡터 스토어 생성
        logger.info("벡터 임베딩을 생성하고 저장하는 중...")
        logger.info("(이 과정은 문서 크기에 따라 수 분이 걸릴 수 있습니다)")
        
        if self.use_cloud:
            # ChromaDB Cloud 사용 - 배치 처리로 OpenAI API 토큰 제한 회피
            logger.info(f"ChromaDB Cloud에 저장합니다 (Collection: {self.collection_name})")
            
            # 배치 크기 설정 (OpenAI API 제한을 고려하여 작은 배치로 처리)
            batch_size = 50  # 한 번에 50개씩 처리
            total_chunks = len(chunks)
            
            # 첫 번째 배치로 컬렉션 생성
            logger.info(f"총 {total_chunks}개의 청크를 {batch_size}개씩 배치로 처리합니다...")
            first_batch = chunks[:batch_size]
            
            self.vectorstore = Chroma.from_documents(
                documents=first_batch,
                embedding=self.embeddings,
                client=self.client,
                collection_name=self.collection_name
            )
            logger.info(f"✓ 배치 1/{(total_chunks + batch_size - 1) // batch_size} 완료 ({len(first_batch)}개 청크)")
            
            # 나머지 청크들을 배치로 추가
            for i in range(batch_size, total_chunks, batch_size):
                batch = chunks[i:i + batch_size]
                batch_num = (i // batch_size) + 1
                total_batches = (total_chunks + batch_size - 1) // batch_size
                
                # 텍스트와 메타데이터 추출
                texts = [doc.page_content for doc in batch]
                metadatas = [doc.metadata for doc in batch]
                
                # 배치 추가
                self.vectorstore.add_texts(texts=texts, metadatas=metadatas)
                logger.info(f"✓ 배치 {batch_num}/{total_batches} 완료 ({len(batch)}개 청크)")
            
            logger.info(f"벡터 스토어가 ChromaDB Cloud에 생성되었습니다 (총 {total_chunks}개 청크).")
        else:
            # 로컬 ChromaDB 사용
            self.vectorstore = Chroma.from_documents(
                documents=chunks,
                embedding=self.embeddings,
                persist_directory=self.persist_directory,
                collection_name=self.collection_name
            )
            logger.info(f"벡터 스토어가 생성되었습니다: {self.persist_directory}")
        
        return self.vectorstore
    
    def load_vectorstore(self) -> Chroma:
        """
        기존 벡터 스토어를 로드합니다.
        
        Returns:
            Chroma 벡터 스토어
        """
        if self.use_cloud:
            # ChromaDB Cloud에서 로드
            logger.info(f"ChromaDB Cloud에서 컬렉션을 로드합니다: {self.collection_name}")
            self.vectorstore = Chroma(
                client=self.client,
                collection_name=self.collection_name,
                embedding_function=self.embeddings
            )
            logger.info("ChromaDB Cloud에서 벡터 스토어를 로드했습니다.")
        else:
            # 로컬에서 로드
            if not os.path.exists(self.persist_directory):
                raise ValueError(f"벡터 스토어가 존재하지 않습니다: {self.persist_directory}")
            
            logger.info(f"벡터 스토어를 로드합니다: {self.persist_directory}")
            self.vectorstore = Chroma(
                persist_directory=self.persist_directory,
                embedding_function=self.embeddings,
                collection_name=self.collection_name
            )
        
        return self.vectorstore
    
    def get_vectorstore(self) -> Optional[Chroma]:
        """현재 벡터 스토어를 반환합니다."""
        return self.vectorstore
    
    def similarity_search(
        self,
        query: str,
        k: int = 4,
        filter_dict: Optional[dict] = None
    ) -> List[tuple]:
        """
        유사도 검색을 수행합니다.
        
        Args:
            query: 검색 쿼리
            k: 반환할 문서 수
            filter_dict: 메타데이터 필터
        
        Returns:
            (문서, 유사도 점수) 튜플 리스트
        """
        if not self.vectorstore:
            raise ValueError("벡터 스토어가 초기화되지 않았습니다.")
        
        # 유사도 점수와 함께 검색
        results = self.vectorstore.similarity_search_with_score(
            query=query,
            k=k,
            filter=filter_dict
        )
        
        return results
    
    def get_retriever(self, search_kwargs: Optional[dict] = None):
        """
        Retriever 객체를 반환합니다.
        
        Args:
            search_kwargs: 검색 옵션
        
        Returns:
            VectorStoreRetriever
        """
        if not self.vectorstore:
            raise ValueError("벡터 스토어가 초기화되지 않았습니다.")
        
        if search_kwargs is None:
            search_kwargs = {"k": 4}
        
        return self.vectorstore.as_retriever(search_kwargs=search_kwargs)
    
    def delete_vectorstore(self):
        """벡터 스토어를 삭제합니다."""
        if self.use_cloud:
            # ChromaDB Cloud에서 컬렉션 삭제
            try:
                self.client.delete_collection(name=self.collection_name)
                logger.info(f"ChromaDB Cloud 컬렉션이 삭제되었습니다: {self.collection_name}")
                self.vectorstore = None
            except Exception as e:
                logger.warning(f"컬렉션 삭제 실패: {e}")
        else:
            # 로컬 벡터 스토어 삭제
            import shutil
            
            if os.path.exists(self.persist_directory):
                shutil.rmtree(self.persist_directory)
                logger.info(f"벡터 스토어가 삭제되었습니다: {self.persist_directory}")
                self.vectorstore = None
            else:
                logger.warning("삭제할 벡터 스토어가 없습니다.")


def test_vector_store():
    """벡터 스토어 테스트 함수"""
    from .document_loader import DocumentLoader
    
    # 문서 로드
    logger.info("문서 로딩 중...")
    loader = DocumentLoader("./reference")
    documents = loader.load_documents()
    
    # 벡터 스토어 생성
    logger.info("벡터 스토어 생성 중...")
    vs_manager = VectorStoreManager()
    vectorstore = vs_manager.create_vectorstore(documents, force_recreate=True)
    
    # 테스트 검색
    test_query = "직원 복무 규정"
    logger.info(f"\n테스트 검색: '{test_query}'")
    results = vs_manager.similarity_search(test_query, k=3)
    
    for i, (doc, score) in enumerate(results, 1):
        print(f"\n결과 {i} (유사도: {score:.4f}):")
        print(f"파일: {doc.metadata.get('filename', 'Unknown')}")
        print(f"카테고리: {doc.metadata.get('category', 'Unknown')}")
        print(f"내용: {doc.page_content[:200]}...")


if __name__ == "__main__":
    test_vector_store()

