"""RAG 체인 구성 모듈"""

import os
from typing import List, Dict, Optional, Tuple
import logging

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

from .vector_store import VectorStoreManager

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# 시스템 프롬프트 템플릿
SYSTEM_PROMPT_TEMPLATE = """당신은 NICE평가정보의 내규 및 규정에 대해 답변하는 친절한 AI 어시스턴트입니다.

답변 가이드라인:

1. **문서 기반 답변**: 제공된 문서 내용을 토대로 정확하게 답변하세요.
2. **유연한 해석**: 문서에 직접적으로 명시되지 않더라도, 관련된 내용을 토대로 합리적인 답변을 제공할 수 있습니다.
3. **명확한 출처**: 답변 시 어떤 규정이나 문서를 참고했는지 언급하세요.
4. **이해하기 쉽게**: 전문 용어는 필요시 쉽게 풀어서 설명하세요.
5. **불확실한 경우**: 문서에서 관련 내용을 찾을 수 없는 경우에만 "제공된 문서에서 해당 내용을 찾을 수 없습니다"라고 답변하세요.

참고 문서:

{context}

질문: {question}

답변:"""


class RAGChain:
    """RAG 체인 클래스"""
    
    def __init__(
        self,
        vector_store_manager: VectorStoreManager,
        model_name: str = "gpt-4-turbo-preview",
        temperature: float = 0,
        similarity_threshold: float = 1.2,  # 더 관대하게 조정 (0.5 -> 1.2)
        top_k: int = 6  # 더 많은 문서 검색 (4 -> 6)
    ):
        """
        Args:
            vector_store_manager: 벡터 스토어 관리자
            model_name: OpenAI 모델 이름
            temperature: 생성 온도 (0=결정적, 1=창의적)
            similarity_threshold: 유사도 임계값 (이하는 범위 밖으로 간주)
            top_k: 검색할 문서 수
        """
        self.vs_manager = vector_store_manager
        self.model_name = model_name
        self.temperature = temperature
        self.similarity_threshold = similarity_threshold
        self.top_k = top_k
        
        # LLM 초기화
        self.llm = ChatOpenAI(
            model_name=model_name,
            temperature=temperature
        )
        
        # 프롬프트 템플릿 설정 (LCEL 방식)
        self.prompt = ChatPromptTemplate.from_template(SYSTEM_PROMPT_TEMPLATE)
        
        # RAG 체인 생성
        self.chain = None
        self.retriever = None
        self._initialize_chain()
    
    def _initialize_chain(self):
        """체인을 초기화합니다."""
        vectorstore = self.vs_manager.get_vectorstore()
        
        if not vectorstore:
            raise ValueError("벡터 스토어가 초기화되지 않았습니다.")
        
        # Retriever 설정
        self.retriever = self.vs_manager.get_retriever(
            search_kwargs={"k": self.top_k}
        )
        
        # 문서를 컨텍스트 문자열로 변환하는 함수
        def format_docs(docs):
            return "\n\n".join(doc.page_content for doc in docs)
        
        # LCEL 체인 구성
        self.chain = (
            {
                "context": self.retriever | format_docs,
                "question": RunnablePassthrough()
            }
            | self.prompt
            | self.llm
            | StrOutputParser()
        )
    
    def query(self, question: str) -> Dict[str, any]:
        """
        질문에 대한 답변을 생성합니다.
        
        Args:
            question: 사용자 질문
        
        Returns:
            답변과 메타데이터를 포함한 딕셔너리
        """
        if not self.chain:
            raise ValueError("RAG 체인이 초기화되지 않았습니다.")
        
        try:
            # 유사도 검색 수행
            search_results = self.vs_manager.similarity_search(
                question,
                k=self.top_k
            )
            
            # 유사도 점수 확인
            if not search_results:
                return {
                    "answer": "죄송합니다. 관련된 문서를 찾을 수 없습니다.",
                    "sources": [],
                    "is_out_of_scope": True,
                    "confidence": 0.0
                }
            
            # 최고 유사도 점수 확인
            best_score = search_results[0][1]
            
            # 임계값 이하인 경우 범위 밖으로 판단
            if best_score > self.similarity_threshold:  # ChromaDB는 거리를 반환 (낮을수록 유사)
                return {
                    "answer": "죄송합니다. 해당 질문은 제공된 NICE평가정보 내규 문서의 범위를 벗어납니다. NICE평가정보의 조직, 인사, 복지, 감사, 업무, IT, 기업평가, 금융소비자 보호 관련 내규에 대해서만 답변드릴 수 있습니다.",
                    "sources": [],
                    "is_out_of_scope": True,
                    "confidence": 0.0
                }
            
            # LCEL 체인 실행
            answer = self.chain.invoke(question)
            
            # 소스 문서 정리 (retriever에서 직접 가져옴)
            source_docs = self.retriever.invoke(question)
            sources = []
            for doc in source_docs:
                sources.append({
                    "filename": doc.metadata.get("filename", "Unknown"),
                    "category": doc.metadata.get("category", "Unknown"),
                    "content_preview": doc.page_content[:200] + "..."
                })
            
            return {
                "answer": answer,
                "sources": sources,
                "is_out_of_scope": False,
                "confidence": 1.0 - best_score  # 거리를 신뢰도로 변환
            }
            
        except Exception as e:
            logger.error(f"쿼리 처리 중 오류 발생: {str(e)}")
            return {
                "answer": f"죄송합니다. 답변 생성 중 오류가 발생했습니다: {str(e)}",
                "sources": [],
                "is_out_of_scope": False,
                "confidence": 0.0
            }
    
    def query_with_filter(
        self,
        question: str,
        category: Optional[str] = None
    ) -> Dict[str, any]:
        """
        카테고리 필터를 적용하여 질문에 답변합니다.
        
        Args:
            question: 사용자 질문
            category: 필터링할 카테고리
        
        Returns:
            답변과 메타데이터를 포함한 딕셔너리
        """
        if category:
            filter_dict = {"category": category}
            search_results = self.vs_manager.similarity_search(
                question,
                k=self.top_k,
                filter_dict=filter_dict
            )
            
            if not search_results:
                return {
                    "answer": f"'{category}' 카테고리에서 관련 문서를 찾을 수 없습니다.",
                    "sources": [],
                    "is_out_of_scope": True,
                    "confidence": 0.0
                }
        
        return self.query(question)


class ConversationalRAGChain(RAGChain):
    """대화형 RAG 체인 클래스"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.conversation_history: List[Dict[str, str]] = []
    
    def query_with_history(self, question: str) -> Dict[str, any]:
        """
        대화 히스토리를 고려하여 답변합니다.
        
        Args:
            question: 사용자 질문
        
        Returns:
            답변과 메타데이터를 포함한 딕셔너리
        """
        # 히스토리를 고려한 컨텍스트 구성
        context_question = question
        if self.conversation_history:
            # 최근 2개의 대화만 포함
            recent_history = self.conversation_history[-2:]
            history_text = "\n".join([
                f"이전 질문: {h['question']}\n이전 답변: {h['answer']}"
                for h in recent_history
            ])
            context_question = f"{history_text}\n\n현재 질문: {question}"
        
        # 쿼리 실행
        result = self.query(context_question)
        
        # 히스토리에 추가
        self.conversation_history.append({
            "question": question,
            "answer": result["answer"]
        })
        
        return result
    
    def clear_history(self):
        """대화 히스토리를 초기화합니다."""
        self.conversation_history = []


def test_rag_chain():
    """RAG 체인 테스트 함수"""
    from .document_loader import DocumentLoader
    
    # 문서 로드
    logger.info("문서 로딩 중...")
    loader = DocumentLoader("./reference")
    documents = loader.load_documents()
    
    # 벡터 스토어 생성/로드
    logger.info("벡터 스토어 초기화 중...")
    vs_manager = VectorStoreManager()
    
    try:
        vs_manager.load_vectorstore()
    except:
        vs_manager.create_vectorstore(documents)
    
    # RAG 체인 초기화
    logger.info("RAG 체인 초기화 중...")
    rag_chain = ConversationalRAGChain(
        vector_store_manager=vs_manager,
        model_name="gpt-3.5-turbo",  # 테스트용으로 저렴한 모델 사용
        temperature=0
    )
    
    # 테스트 질문들
    test_questions = [
        "직원의 복무 규정에 대해 알려주세요",
        "연차 휴가는 어떻게 사용하나요?",
        "오늘 날씨는 어때요?",  # 범위 밖 질문
    ]
    
    for question in test_questions:
        print(f"\n{'='*60}")
        print(f"질문: {question}")
        print(f"{'='*60}")
        
        result = rag_chain.query(question)
        
        print(f"\n답변: {result['answer']}")
        print(f"\n범위 밖 여부: {result['is_out_of_scope']}")
        print(f"신뢰도: {result['confidence']:.4f}")
        
        if result['sources']:
            print(f"\n참고 문서:")
            for i, source in enumerate(result['sources'], 1):
                print(f"  {i}. {source['filename']} ({source['category']})")


if __name__ == "__main__":
    test_rag_chain()

