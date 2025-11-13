"""NICE평가정보 내규 챗봇 - Streamlit UI"""

import os
import sys
from pathlib import Path
import logging

import streamlit as st
from dotenv import load_dotenv

from src.document_loader import DocumentLoader
from src.vector_store import VectorStoreManager
from src.rag_chain import ConversationalRAGChain

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 환경 변수 로드 (로컬: .env, Streamlit Cloud: secrets)
load_dotenv()

# Streamlit Cloud Secrets 지원 함수
def get_env(key: str, default: str = None) -> str:
    """환경 변수 가져오기 (Streamlit Secrets 우선, 그 다음 .env)"""
    # Streamlit Cloud secrets 확인
    if hasattr(st, 'secrets') and key in st.secrets:
        return st.secrets[key]
    # 로컬 .env 파일
    return os.getenv(key, default)

# 페이지 설정
st.set_page_config(
    page_title="NICE평가정보 내규 챗봇",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 스타일 설정
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    .user-message {
        background-color: #e3f2fd;
    }
    .assistant-message {
        background-color: #f5f5f5;
    }
    .source-box {
        background-color: #fff3cd;
        padding: 0.5rem;
        border-radius: 0.3rem;
        margin-top: 0.5rem;
        font-size: 0.9rem;
    }
    .warning-box {
        background-color: #fff3cd;
        border-left: 4px solid #ffc107;
        padding: 1rem;
        margin: 1rem 0;
    }
    .stButton > button {
        border-radius: 8px;
        border: 1px solid #e0e0e0;
        padding: 0.75rem 1rem;
        transition: all 0.3s ease;
    }
    .stButton > button:hover {
        background-color: #e3f2fd;
        border-color: #1f77b4;
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)


def initialize_session_state():
    """세션 상태 초기화"""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    if "rag_chain" not in st.session_state:
        st.session_state.rag_chain = None
    
    if "vectorstore_loaded" not in st.session_state:
        st.session_state.vectorstore_loaded = False
    
    if "show_sources" not in st.session_state:
        st.session_state.show_sources = True
    
    if "selected_question" not in st.session_state:
        st.session_state.selected_question = None


def initialize_rag_system():
    """RAG 시스템 초기화"""
    try:
        with st.spinner("RAG 시스템을 초기화하는 중..."):
            # API 키 확인
            if not get_env("OPENAI_API_KEY"):
                st.error("⚠️ OPENAI_API_KEY가 설정되지 않았습니다. .env 파일 또는 Streamlit Secrets를 확인하세요.")
                st.stop()
            
            # ChromaDB Cloud 설정 확인
            use_cloud = get_env("CHROMA_API_KEY") is not None
            
            if use_cloud:
                st.info("🌐 ChromaDB Cloud를 사용합니다.")
                # 벡터 스토어 관리자 초기화 (ChromaDB Cloud)
                vs_manager = VectorStoreManager(
                    chunk_size=1500,  # 더 큰 청크로 변경 (1000 -> 1500)
                    chunk_overlap_percent=10.0,  # 더 많은 오버랩 (4% -> 10%)
                    use_cloud=True,
                    cloud_api_key=get_env("CHROMA_API_KEY"),
                    cloud_tenant=get_env("CHROMA_TENANT"),
                    cloud_database=get_env("CHROMA_DATABASE"),
                    collection_name=get_env("CHROMA_COLLECTION", "niceinfo-rules")
                )
            else:
                # st.info("💻 로컬 ChromaDB를 사용합니다.")
                # 벡터 스토어 관리자 초기화 (로컬)
                vs_manager = VectorStoreManager(
                    persist_directory="./chroma_db",
                    chunk_size=1500,  # 더 큰 청크로 변경 (1000 -> 1500)
                    chunk_overlap_percent=10.0,  # 더 많은 오버랩 (4% -> 10%)
                    use_cloud=False
                )
            
            # 기존 벡터 스토어 로드 시도
            if use_cloud:
                # ChromaDB Cloud에서 로드
                try:
                    vs_manager.load_vectorstore()
                    st.session_state.vectorstore_loaded = True
                    logger.info("ChromaDB Cloud에서 벡터 스토어를 로드했습니다.")
                    st.success("✅ ChromaDB Cloud에서 데이터를 로드했습니다!")
                except Exception as e:
                    logger.error(f"벡터 스토어 로드 실패: {e}")
                    st.error(f"❌ ChromaDB Cloud에서 데이터를 로드할 수 없습니다.")
                    st.error(f"오류: {str(e)}")
                    st.warning("⚠️ 먼저 문서를 업로드해야 합니다!")
                    st.info("💡 다음 명령어를 실행하세요:")
                    st.code("python upload_to_chromadb.py", language="bash")
                    st.stop()
            elif Path("./chroma_db").exists():
                # 로컬 ChromaDB 로드
                try:
                    vs_manager.load_vectorstore()
                    st.session_state.vectorstore_loaded = True
                    logger.info("로컬 벡터 스토어를 로드했습니다.")
                    st.success("✅ 로컬 ChromaDB에서 데이터를 로드했습니다!")
                except Exception as e:
                    logger.error(f"벡터 스토어 로드 실패: {e}")
                    st.error(f"❌ 로컬 ChromaDB에서 데이터를 로드할 수 없습니다.")
                    st.warning("⚠️ 먼저 문서를 인덱싱해야 합니다!")
                    st.info("💡 다음 명령어를 실행하세요:")
                    st.code("python setup_db.py", language="bash")
                    st.stop()
            else:
                # 로컬 ChromaDB가 없는 경우
                st.error("❌ 벡터 데이터베이스를 찾을 수 없습니다.")
                st.warning("⚠️ 먼저 문서를 인덱싱해야 합니다!")
                st.info("💡 다음 명령어를 실행하세요:")
                st.code("python setup_db.py", language="bash")
                st.stop()
            
            # RAG 체인 초기화
            rag_chain = ConversationalRAGChain(
                vector_store_manager=vs_manager,
                model_name=get_env("OPENAI_MODEL", "gpt-4-turbo-preview"),
                temperature=0,
                similarity_threshold=1.2,  # 더 관대하게 (0.5 -> 1.2)
                top_k=6  # 더 많은 컨텍스트 (4 -> 6)
            )
            
            st.session_state.rag_chain = rag_chain
            
            return True
            
    except Exception as e:
        st.error(f"❌ 초기화 중 오류 발생: {str(e)}")
        logger.error(f"초기화 오류: {e}", exc_info=True)
        return False


def display_message(role: str, content: str, sources: list = None):
    """메시지 표시"""
    if role == "user":
        st.markdown(f"""
        <div class="chat-message user-message">
            <strong>👤 사용자:</strong><br>
            {content}
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="chat-message assistant-message">
            <strong>🤖 AI 어시스턴트:</strong><br>
            {content}
        </div>
        """, unsafe_allow_html=True)
        
        # 출처 표시
        if sources and st.session_state.show_sources:
            with st.expander("📄 참고 문서 보기", expanded=False):
                for i, source in enumerate(sources, 1):
                    st.markdown(f"""
                    **{i}. {source['filename']}** (카테고리: {source['category']})
                    
                    *미리보기:* {source['content_preview']}
                    """)


def sidebar():
    """사이드바 UI"""
    with st.sidebar:
        st.markdown("## ⚙️ 설정")
        
        # 출처 표시 옵션
        st.session_state.show_sources = st.checkbox(
            "참고 문서 표시",
            value=st.session_state.show_sources,
            help="답변과 함께 참고한 문서를 표시합니다"
        )
        
        st.markdown("---")
        
        # 대화 초기화 버튼
        if st.button("🗑️ 대화 내역 지우기", use_container_width=True):
            st.session_state.messages = []
            if st.session_state.rag_chain:
                st.session_state.rag_chain.clear_history()
            st.rerun()
        
        # 문서 재업로드 안내
        use_cloud = get_env("CHROMA_API_KEY") is not None
        
        if use_cloud:
            # ChromaDB Cloud 사용 시
            if st.button("🔄 문서 재업로드", use_container_width=True):
                st.info("💡 문서를 다시 업로드하려면 다음 스크립트를 실행하세요:")
                st.code("python upload_to_chromadb.py", language="bash")
                st.warning("⚠️ 이 작업은 터미널에서 실행해야 합니다.")
        else:
            # 로컬 ChromaDB 사용 시
            if st.button("🔄 문서 재인덱싱", use_container_width=True):
                st.info("💡 문서를 다시 인덱싱하려면 다음 스크립트를 실행하세요:")
                st.code("python setup_db.py", language="bash")
                st.warning("⚠️ 이 작업은 터미널에서 실행해야 합니다.")
        
        st.markdown("---")
        
        # 사용 안내
        st.markdown("""
        ### 📖 사용 안내
        
        이 챗봇은 NICE평가정보의 다음 내규에 대해 답변합니다:
        
        - 📋 조직 관련 규정
        - 👥 인사 관련 규정
        - 💰 복지 관련 규정
        - 🔍 감사 관련 규정
        - 💼 업무 관련 규정
        - 💻 IT 관련 규정
        - 🏢 기업평가 관련 규정
        - 🏦 금융소비자 보호 규정
        
        **주의사항:**
        - 제공된 문서 범위 내에서만 답변합니다
        - 문서에 없는 내용은 답변하지 않습니다
        - 정확한 답변을 위해 구체적으로 질문해주세요
        """)
        
        st.markdown("---")
        
        # 시스템 정보
        if st.session_state.vectorstore_loaded:
            st.success("✅ 시스템 준비 완료")
        # else:
        #     st.warning("⚠️ 시스템 초기화 필요")
        
        # ChromaDB 정보 표시
        use_cloud = get_env("CHROMA_API_KEY") is not None
        db_type = "ChromaDB Cloud" if use_cloud else "ChromaDB Local"
        
        st.markdown(f"""
        <div style="font-size: 0.8rem; color: #666; margin-top: 2rem;">
        Powered by OpenAI & LangChain<br>
        Vector DB: {db_type}
        </div>
        """, unsafe_allow_html=True)


def main():
    """메인 함수"""
    # 세션 상태 초기화
    initialize_session_state()
    
    # 헤더
    st.markdown('<div class="main-header">📚 NICE평가정보 내규 챗봇</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">내규 및 규정에 대해 무엇이든 물어보세요</div>', unsafe_allow_html=True)
    
    # 사이드바
    sidebar()
    
    # RAG 시스템 초기화 (아직 안 된 경우)
    if st.session_state.rag_chain is None:
        if not initialize_rag_system():
            st.stop()
    
    # 경고 메시지
    st.markdown("""
    <div class="warning-box">
        ⚠️ <strong>중요:</strong> 이 챗봇은 제공된 NICE평가정보 내규 문서에만 기반하여 답변합니다. 
        문서 범위를 벗어난 질문에는 답변하지 않습니다.
    </div>
    """, unsafe_allow_html=True)
    
    # 예시 질문 (대화 시작 전에만 표시)
    if len(st.session_state.messages) == 0:
        st.markdown("### 💡 예시 질문")
        st.markdown("궁금하신 내용을 클릭해보세요:")
        
        # 예시 질문 리스트
        example_questions = [
            "직원 복무 규정에 대해 알려주세요",
            "연차 휴가는 어떻게 사용하나요?",
            "급여는 언제 지급되나요?",
            "퇴직금 지급 규정은 무엇인가요?",
            "승진 규정에 대해 설명해주세요",
            "복지후생 혜택은 어떤 것이 있나요?",
        ]
        
        # 2열로 버튼 배치
        col1, col2 = st.columns(2)
        
        for idx, question in enumerate(example_questions):
            col = col1 if idx % 2 == 0 else col2
            with col:
                if st.button(f"💬 {question}", key=f"example_{idx}", use_container_width=True):
                    # 세션 상태에 선택된 질문 저장
                    st.session_state.selected_question = question
                    st.rerun()
        
        st.markdown("---")
    
    # 선택된 예시 질문 처리
    if hasattr(st.session_state, 'selected_question') and st.session_state.selected_question:
        prompt = st.session_state.selected_question
        st.session_state.selected_question = None  # 한 번만 처리
        
        # 사용자 메시지 추가
        st.session_state.messages.append({
            "role": "user",
            "content": prompt
        })
        display_message("user", prompt)
        
        # AI 응답 생성
        with st.spinner("답변을 생성하는 중..."):
            try:
                result = st.session_state.rag_chain.query_with_history(prompt)
                
                # 어시스턴트 메시지 추가
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": result["answer"],
                    "sources": result["sources"],
                    "is_out_of_scope": result["is_out_of_scope"],
                    "confidence": result["confidence"]
                })
                
                display_message(
                    "assistant",
                    result["answer"],
                    result["sources"]
                )
                
                # 범위 밖 경고
                if result["is_out_of_scope"]:
                    st.warning("⚠️ 이 질문은 제공된 문서 범위를 벗어납니다.")
                
            except Exception as e:
                error_msg = f"죄송합니다. 답변 생성 중 오류가 발생했습니다: {str(e)}"
                st.error(error_msg)
                logger.error(f"쿼리 처리 오류: {e}", exc_info=True)
                
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": error_msg,
                    "sources": [],
                    "is_out_of_scope": False,
                    "confidence": 0.0
                })
        
        st.rerun()
    
    # 대화 내역 표시
    for message in st.session_state.messages:
        display_message(
            message["role"],
            message["content"],
            message.get("sources", [])
        )
    
    # 사용자 입력
    if prompt := st.chat_input("내규에 대해 궁금한 점을 물어보세요..."):
        # 사용자 메시지 추가
        st.session_state.messages.append({
            "role": "user",
            "content": prompt
        })
        display_message("user", prompt)
        
        # AI 응답 생성
        with st.spinner("답변을 생성하는 중..."):
            try:
                result = st.session_state.rag_chain.query_with_history(prompt)
                
                # 어시스턴트 메시지 추가
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": result["answer"],
                    "sources": result["sources"],
                    "is_out_of_scope": result["is_out_of_scope"],
                    "confidence": result["confidence"]
                })
                
                display_message(
                    "assistant",
                    result["answer"],
                    result["sources"]
                )
                
                # 범위 밖 경고
                if result["is_out_of_scope"]:
                    st.warning("⚠️ 이 질문은 제공된 문서 범위를 벗어납니다.")
                
            except Exception as e:
                error_msg = f"죄송합니다. 답변 생성 중 오류가 발생했습니다: {str(e)}"
                st.error(error_msg)
                logger.error(f"쿼리 처리 오류: {e}", exc_info=True)
                
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": error_msg,
                    "sources": [],
                    "is_out_of_scope": False,
                    "confidence": 0.0
                })


if __name__ == "__main__":
    main()

