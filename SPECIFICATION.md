# NICE평가정보 내규 챗봇 시스템 명세서

**버전**: 1.0  
**작성일**: 2025-11-11  
**작성자**: AI Development Team

---

## 목차

1. [개요](#1-개요)
2. [시스템 아키텍처](#2-시스템-아키텍처)
3. [기능 요구사항](#3-기능-요구사항)
4. [비기능 요구사항](#4-비기능-요구사항)
5. [모듈 명세](#5-모듈-명세)
6. [데이터 명세](#6-데이터-명세)
7. [인터페이스 명세](#7-인터페이스-명세)
8. [배포 명세](#8-배포-명세)
9. [테스트 요구사항](#9-테스트-요구사항)

---

## 1. 개요

### 1.1 목적

`./reference` 폴더 내의 NICE평가정보 내규 문서를 기반으로 질의응답하는 RAG(Retrieval-Augmented Generation) 챗봇 시스템 구축.

### 1.2 범위

- **포함**: ZIP 파일을 제외한 모든 문서 (.doc, .docx, .xlsx, .pdf)
- **제외**: ZIP 파일 및 지원하지 않는 형식
- **답변 범위**: 제공된 문서 내용에만 한정
- **범위 밖 처리**: 명확한 안내 메시지 제공

### 1.3 핵심 제약사항

1. **문서 범위 제한**: 제공된 내규 문서 외의 내용은 답변하지 않음
2. **출처 투명성**: 모든 답변에 참고 문서 명시
3. **정확성 우선**: 추측보다 "모름" 답변 선호

### 1.4 기술 스택

| 구분 | 기술 | 버전 |
|------|------|------|
| 언어 | Python | 3.8+ |
| RAG 프레임워크 | LangChain | 0.1.0 |
| LLM | OpenAI GPT-4 | API |
| 임베딩 | OpenAI Embeddings | text-embedding-3-small |
| 벡터 DB | ChromaDB | 0.4.22 |
| UI | Streamlit | 1.29.0 |
| 문서 파싱 | python-docx, openpyxl, PyPDF2 | - |

---

## 2. 시스템 아키텍처

### 2.1 전체 아키텍처

```
┌─────────────────────────────────────────────────────────┐
│                    Streamlit Web UI                     │
│                       (app.py)                          │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│                 RAG Chain Layer                         │
│                  (rag_chain.py)                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │ ConversationalRAGChain                           │  │
│  │  - query_with_history()                          │  │
│  │  - conversation_history management               │  │
│  └──────────────────────────────────────────────────┘  │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│              Vector Store Layer                         │
│               (vector_store.py)                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │ VectorStoreManager                               │  │
│  │  - similarity_search()                           │  │
│  │  - get_retriever()                               │  │
│  └──────────────────────────────────────────────────┘  │
│                       │                                 │
│              ┌────────┴────────┐                        │
│              ▼                 ▼                        │
│      ┌─────────────┐   ┌──────────────┐               │
│      │  ChromaDB   │   │   OpenAI     │               │
│      │  (Vector)   │   │  (Embedding) │               │
│      └─────────────┘   └──────────────┘               │
└─────────────────────────────────────────────────────────┘
                     ▲
                     │
┌────────────────────┴────────────────────────────────────┐
│            Document Loader Layer                        │
│             (document_loader.py)                        │
│  ┌──────────────────────────────────────────────────┐  │
│  │ DocumentLoader                                   │  │
│  │  - load_documents()                              │  │
│  │  - parse by format (.doc, .docx, .xlsx, .pdf)   │  │
│  └──────────────────────────────────────────────────┘  │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│             ./reference/ (Documents)                    │
│   ┌──────────┬──────────┬──────────┬──────────┐       │
│   │   .doc   │  .docx   │  .xlsx   │   .pdf   │       │
│   └──────────┴──────────┴──────────┴──────────┘       │
│              (exclude .zip files)                       │
└─────────────────────────────────────────────────────────┘
```

### 2.2 데이터 플로우

#### 2.2.1 초기화 플로우

```
1. Document Loading
   reference/*.{doc,docx,xlsx,pdf}
   → DocumentLoader.load_documents()
   → List[LangchainDocument]

2. Text Chunking
   Documents
   → RecursiveCharacterTextSplitter(chunk_size=1000, overlap=200)
   → List[Chunk]

3. Embedding & Indexing
   Chunks
   → OpenAI Embeddings API
   → ChromaDB.persist()
   → ./chroma_db/

4. RAG Chain Setup
   ChromaDB Retriever + OpenAI LLM
   → RetrievalQA Chain
   → Ready for Queries
```

#### 2.2.2 쿼리 플로우

```
1. User Input
   Question (string)
   → Streamlit UI

2. Query Embedding
   Question
   → OpenAI Embeddings API
   → Vector

3. Similarity Search
   Query Vector
   → ChromaDB.similarity_search_with_score(k=4)
   → [(Document, Score), ...]

4. Relevance Check
   if best_score > threshold (0.5):
      → Out of Scope Response
   else:
      → Continue

5. Context Building
   Retrieved Documents
   → Prompt Template with Context
   → Full Prompt

6. LLM Generation
   Prompt
   → OpenAI GPT-4 API
   → Answer

7. Response
   Answer + Sources
   → Streamlit UI
```

### 2.3 디렉토리 구조

```
niceinfo-rules-chatbot/
├── src/                        # 소스 코드 모듈
│   ├── __init__.py
│   ├── utils.py                # 유틸리티 함수
│   ├── document_loader.py      # 문서 로더
│   ├── vector_store.py         # 벡터 스토어
│   └── rag_chain.py            # RAG 체인
│
├── reference/                  # 문서 저장소 (사용자 제공)
│   └── [내규 문서들]/
│
├── chroma_db/                  # 벡터 DB (자동 생성)
│   └── [ChromaDB 파일들]/
│
├── app.py                      # Streamlit 메인 앱
├── setup_db.py                 # DB 초기 설정 스크립트
├── check_system.py             # 시스템 체크 스크립트
├── run.py                      # 실행 헬퍼 스크립트
├── start_chatbot.bat           # Windows 배치 파일
│
├── requirements.txt            # Python 의존성
├── .env                        # 환경 변수 (생성 필요)
├── env_template.txt            # 환경 변수 템플릿
├── .gitignore                  # Git 제외 파일
│
└── [문서 파일들]/              # 프로젝트 문서
    ├── README.md
    ├── QUICKSTART.md
    ├── EXAMPLES.md
    ├── PROJECT_SUMMARY.md
    └── SPECIFICATION.md
```

---

## 3. 기능 요구사항

### 3.1 문서 처리 (FR-DOC)

#### FR-DOC-001: 문서 탐색
- **설명**: reference 폴더를 재귀적으로 탐색하여 모든 문서 파일 검색
- **입력**: 루트 디렉토리 경로 (string)
- **출력**: 파일 경로 리스트 (List[Path])
- **제약**: 
  - .zip 파일은 자동 제외
  - 숨김 파일/폴더는 제외

#### FR-DOC-002: 파일 형식 지원
- **지원 형식**:
  - `.doc` (MS Word 레거시)
  - `.docx` (MS Word)
  - `.xlsx` (MS Excel)
  - `.xls` (MS Excel 레거시)
  - `.pdf` (PDF)
- **제외 형식**:
  - `.zip` (명시적 제외)
  - 기타 모든 형식

#### FR-DOC-003: 문서 파싱
- **DOCX 파싱**:
  - 라이브러리: python-docx
  - 추출 대상: 본문 텍스트, 표 내용
  - Fallback: docx2txt
  
- **DOC 파싱**:
  - 라이브러리: win32com.client (Windows only)
  - 방법: COM 인터페이스로 Word 자동화
  - 비Windows: 건너뛰기 (경고 로그)

- **XLSX 파싱**:
  - 라이브러리: openpyxl
  - 추출 대상: 모든 시트의 셀 값
  - 형식: 시트명 + 행 데이터

- **PDF 파싱**:
  - 라이브러리: PyPDF2
  - 추출 대상: 텍스트 내용
  - 제약: 이미지/차트는 제외

#### FR-DOC-004: 메타데이터 추출
- **필수 메타데이터**:
  ```python
  {
      'source': str,        # 파일 전체 경로
      'filename': str,      # 파일명만
      'category': str,      # 카테고리 (폴더명에서 추출)
      'file_type': str      # 파일 확장자
  }
  ```
- **카테고리 추출 규칙**:
  - 패턴: `N)_카테고리명_X` → "카테고리명"
  - 예: `1)_조직_11` → "조직"
  - 기본값: "기타"

#### FR-DOC-005: 텍스트 정리
- **수행 작업**:
  - 과도한 공백 제거
  - 연속 빈 줄 제한 (최대 2줄)
  - 앞뒤 공백 trim

### 3.2 벡터 스토어 (FR-VEC)

#### FR-VEC-001: 텍스트 청킹
- **청킹 파라미터**:
  ```python
  chunk_size = 1000        # 글자
  chunk_overlap = 200      # 글자
  separators = ["\n\n", "\n", "。", ".", " ", ""]
  ```
- **방법**: RecursiveCharacterTextSplitter
- **목적**: 의미 단위 분할, 검색 정확도 향상

#### FR-VEC-002: 임베딩 생성
- **모델**: text-embedding-3-small (OpenAI)
- **입력**: 텍스트 청크
- **출력**: 1536차원 벡터
- **API**: OpenAI Embeddings API

#### FR-VEC-003: 벡터 저장
- **데이터베이스**: ChromaDB
- **저장 위치**: `./chroma_db/`
- **컬렉션명**: `niceinfo_rules`
- **영속성**: 파일 기반 (persist_directory)

#### FR-VEC-004: 유사도 검색
- **메소드**: `similarity_search_with_score()`
- **파라미터**:
  - `query`: 검색 쿼리 (string)
  - `k`: 반환할 문서 수 (default: 4)
  - `filter`: 메타데이터 필터 (optional)
- **출력**: `List[Tuple[Document, float]]`
- **거리 메트릭**: L2 (낮을수록 유사)

#### FR-VEC-005: 벡터 DB 관리
- **생성**: `create_vectorstore(force_recreate)`
- **로드**: `load_vectorstore()`
- **삭제**: `delete_vectorstore()`
- **상태 확인**: 디렉토리 존재 여부

### 3.3 RAG 체인 (FR-RAG)

#### FR-RAG-001: 프롬프트 템플릿
```python
SYSTEM_PROMPT_TEMPLATE = """
당신은 NICE평가정보의 내규 및 규정에 대해 답변하는 AI 어시스턴트입니다.

다음 규칙을 반드시 따라야 합니다:

1. 제공된 문서 내용만을 기반으로 정확하게 답변해야 합니다.
2. 문서에 없는 내용이나 확실하지 않은 내용에 대해서는 
   "제공된 내규 문서에서 해당 내용을 찾을 수 없습니다" 또는 
   "해당 내용은 제공된 문서 범위를 벗어납니다"라고 명확히 답변해야 합니다.
3. 답변할 때는 어떤 문서(파일명 또는 규정명)를 참고했는지 명시하면 좋습니다.
4. 전문적이고 정확한 톤으로 답변하되, 이해하기 쉽게 설명해야 합니다.
5. 추측이나 일반적인 지식으로 답변하지 말고, 
   반드시 제공된 문서에 근거해야 합니다.

아래는 질문과 관련된 문서 내용입니다:

{context}

질문: {question}

답변:"""
```

#### FR-RAG-002: 범위 판단 로직
```python
# 유사도 임계값
SIMILARITY_THRESHOLD = 0.5

# 판단 로직
if not search_results or best_score > SIMILARITY_THRESHOLD:
    return OUT_OF_SCOPE_RESPONSE
```

#### FR-RAG-003: 범위 밖 응답
```
"죄송합니다. 해당 질문은 제공된 NICE평가정보 내규 문서의 범위를 벗어납니다. 
NICE평가정보의 조직, 인사, 복지, 감사, 업무, IT, 기업평가, 
금융소비자 보호 관련 내규에 대해서만 답변드릴 수 있습니다."
```

#### FR-RAG-004: LLM 설정
- **모델**: gpt-4-turbo-preview (default)
- **온도**: 0 (결정적 답변)
- **체인 타입**: "stuff" (모든 문서를 프롬프트에 포함)

#### FR-RAG-005: 대화 히스토리
- **저장**: 세션 기반 리스트
- **형식**: `[{'question': str, 'answer': str}, ...]`
- **활용**: 최근 2개 대화만 컨텍스트에 포함
- **초기화**: `clear_history()` 메소드

#### FR-RAG-006: 응답 형식
```python
{
    "answer": str,              # 생성된 답변
    "sources": List[dict],      # 참고 문서 목록
    "is_out_of_scope": bool,    # 범위 밖 여부
    "confidence": float         # 신뢰도 (0-1)
}

# sources 형식
{
    "filename": str,            # 파일명
    "category": str,            # 카테고리
    "content_preview": str      # 내용 미리보기 (200자)
}
```

### 3.4 사용자 인터페이스 (FR-UI)

#### FR-UI-001: 페이지 구성
- **헤더**: 제목 + 부제목
- **메인**: 채팅 영역
- **사이드바**: 설정 및 컨트롤
- **입력창**: 하단 고정

#### FR-UI-002: 채팅 인터페이스
- **메시지 형식**:
  - 사용자: 파란색 배경 + 👤 아이콘
  - AI: 회색 배경 + 🤖 아이콘
- **출처 표시**: 확장 가능한 섹션
- **스크롤**: 자동 하단 이동

#### FR-UI-003: 세션 상태 관리
```python
st.session_state = {
    'messages': List[dict],         # 대화 내역
    'rag_chain': RAGChain,          # RAG 체인 인스턴스
    'vectorstore_loaded': bool,     # 벡터 DB 로드 상태
    'show_sources': bool            # 출처 표시 설정
}
```

#### FR-UI-004: 사이드바 기능
1. **참고 문서 표시**: 체크박스
2. **대화 내역 지우기**: 버튼
3. **문서 재인덱싱**: 버튼
4. **사용 안내**: 정적 텍스트
5. **시스템 상태**: 상태 표시기

#### FR-UI-005: 초기화 프로세스
```python
1. 환경 변수 로드 (.env)
2. API 키 확인
3. 벡터 스토어 로드 시도
   - 실패 시: 문서 로드 → 벡터화
4. RAG 체인 초기화
5. UI 렌더링
```

#### FR-UI-006: 에러 처리
- **API 키 없음**: st.error() + st.stop()
- **문서 없음**: st.error() + st.stop()
- **쿼리 실패**: st.error() + 에러 메시지 표시
- **일반 오류**: 로그 + 사용자 친화적 메시지

### 3.5 유틸리티 기능 (FR-UTIL)

#### FR-UTIL-001: 시스템 체크
- **체크 항목**:
  1. Python 버전 (≥3.8)
  2. 패키지 설치 여부
  3. .env 파일 존재
  4. OPENAI_API_KEY 설정
  5. reference 폴더 존재
  6. 문서 파일 개수
  7. 벡터 DB 존재 (선택)
  8. Windows 환경 (win32com)
- **출력**: 체크 결과 + 해결 방안

#### FR-UTIL-002: DB 초기 설정
- **기능**:
  1. 환경 검증
  2. 기존 DB 확인 및 삭제 옵션
  3. 문서 로드 + 통계
  4. 벡터 DB 생성
  5. 테스트 검색
- **인터랙션**: 사용자 확인 (y/N)

#### FR-UTIL-003: 실행 헬퍼
- **사전 확인**:
  - Python 버전
  - .env 파일
  - reference 폴더
  - 패키지 설치
- **실행**: `streamlit run app.py`
- **에러**: 문제 목록 + 해결 방안

---

## 4. 비기능 요구사항

### 4.1 성능 (NFR-PERF)

#### NFR-PERF-001: 초기 로딩 시간
- **문서 로딩**: 100개 문서 기준 1-2분
- **벡터화**: 100개 문서 기준 5-10분
- **벡터 DB 로드**: 5초 이내

#### NFR-PERF-002: 쿼리 응답 시간
- **유사도 검색**: 0.5초 이내
- **LLM 응답**: 2-5초
- **전체 응답**: 3-6초

#### NFR-PERF-003: 메모리 사용량
- **벡터 DB**: 문서 크기의 약 2-3배
- **런타임**: 500MB ~ 2GB

### 4.2 확장성 (NFR-SCAL)

#### NFR-SCAL-001: 문서 확장
- **지원 문서 수**: 최대 1,000개 (권장)
- **문서 크기**: 개당 최대 10MB (권장)
- **총 크기**: 최대 1GB (권장)

#### NFR-SCAL-002: 동시 사용자
- **Streamlit 기본**: 단일 프로세스
- **확장**: 멀티프로세스 배포 필요

### 4.3 가용성 (NFR-AVAIL)

#### NFR-AVAIL-001: 의존성
- **OpenAI API**: 99.9% 가용성 (외부 의존)
- **로컬 시스템**: 벡터 DB 파일 무결성

#### NFR-AVAIL-002: 오류 복구
- **벡터 DB 손상**: 재생성 기능 제공
- **API 오류**: 명확한 에러 메시지
- **문서 파싱 실패**: 건너뛰기 + 로그

### 4.4 보안 (NFR-SEC)

#### NFR-SEC-001: API 키 관리
- **저장**: .env 파일 (gitignore)
- **접근**: 환경 변수로만
- **노출 방지**: 코드에 하드코딩 금지

#### NFR-SEC-002: 데이터 전송
- **OpenAI API**: HTTPS 통신
- **로컬 저장**: 파일 시스템 권한

#### NFR-SEC-003: 문서 보안
- **경고**: 민감 문서는 OpenAI로 전송됨
- **권장**: 내부망 배포 또는 로컬 LLM 고려

### 4.5 유지보수성 (NFR-MAINT)

#### NFR-MAINT-001: 코드 품질
- **모듈화**: 단일 책임 원칙
- **문서화**: Docstring (모든 public 함수)
- **로깅**: INFO 레벨 (중요 이벤트)
- **에러 핸들링**: try-except + 명확한 메시지

#### NFR-MAINT-002: 설정 관리
- **환경 변수**: .env 파일
- **상수**: 모듈 상단 또는 config 파일
- **하드코딩 금지**: 모든 설정값은 변수화

### 4.6 사용성 (NFR-USAB)

#### NFR-USAB-001: 사용자 인터페이스
- **직관성**: 채팅 인터페이스 (일반적 패턴)
- **피드백**: 로딩 스피너, 상태 메시지
- **에러 메시지**: 사용자 친화적 언어

#### NFR-USAB-002: 문서화
- **README**: 설치 및 사용법
- **QUICKSTART**: 3단계 시작 가이드
- **EXAMPLES**: 질문 예제
- **SPECIFICATION**: 기술 명세 (본 문서)

---

## 5. 모듈 명세

### 5.1 src/utils.py

#### 함수: get_all_documents()

```python
def get_all_documents(
    root_dir: str, 
    exclude_extensions: List[str] = None
) -> List[Path]:
    """
    지정된 디렉토리에서 모든 문서 파일을 재귀적으로 찾습니다.
    
    Args:
        root_dir: 검색할 루트 디렉토리
        exclude_extensions: 제외할 파일 확장자 리스트 (예: ['.zip'])
    
    Returns:
        파일 경로 리스트 (정렬됨)
        
    Raises:
        ValueError: 디렉토리가 존재하지 않는 경우
    
    Implementation:
        1. exclude_extensions 기본값: ['.zip']
        2. root_path = Path(root_dir)
        3. 존재 여부 확인
        4. supported_extensions = ['.doc', '.docx', '.xlsx', '.xls', '.pdf']
        5. root_path.rglob('*')로 모든 파일 탐색
        6. 파일이고 + 지원 확장자이고 + 제외 목록에 없으면 추가
        7. 정렬 후 반환
    """
```

#### 함수: extract_category_from_path()

```python
def extract_category_from_path(file_path: Path, root_dir: str) -> str:
    """
    파일 경로에서 카테고리를 추출합니다.
    
    Args:
        file_path: 파일 경로
        root_dir: 루트 디렉토리
    
    Returns:
        카테고리 문자열
        
    Implementation:
        1. relative_path = file_path.relative_to(root_dir)
        2. parts = relative_path.parts
        3. 첫 번째 폴더명 추출
        4. 패턴 매칭: "N)_카테고리_X" → "카테고리"
        5. 실패 시: "기타"
    """
```

#### 함수: clean_text()

```python
def clean_text(text: str) -> str:
    """
    텍스트를 정리합니다.
    
    Args:
        text: 원본 텍스트
    
    Returns:
        정리된 텍스트
        
    Implementation:
        1. 각 줄 strip()
        2. 빈 줄 카운트
        3. 연속 빈 줄 3개 이상 → 2개로 축소
        4. 재결합 후 반환
    """
```

### 5.2 src/document_loader.py

#### 클래스: DocumentLoader

```python
class DocumentLoader:
    """문서 로더 클래스"""
    
    def __init__(self, root_dir: str):
        """
        Args:
            root_dir: 문서가 있는 루트 디렉토리
            
        Attributes:
            self.root_dir: str
            self.supported_parsers: Dict[str, Callable]
        """
    
    def load_documents(self) -> List[LangchainDocument]:
        """
        모든 문서를 로드하고 파싱합니다.
        
        Returns:
            LangchainDocument 리스트
            
        Implementation:
            1. get_all_documents()로 파일 목록 획득
            2. 각 파일에 대해 _load_single_document() 호출
            3. 성공/실패 로그
            4. 통계 출력
            5. 실패 목록 출력
        """
    
    def _load_single_document(self, file_path: Path) -> Optional[LangchainDocument]:
        """
        단일 문서를 로드합니다.
        
        Args:
            file_path: 파일 경로
        
        Returns:
            LangchainDocument 또는 None
            
        Implementation:
            1. 확장자 추출
            2. 해당 파서 선택
            3. 텍스트 추출
            4. clean_text() 호출
            5. 메타데이터 생성
            6. LangchainDocument 반환
        """
    
    def _parse_docx(self, file_path: Path) -> str:
        """
        DOCX 파일 파싱
        
        Implementation:
            1. Document(file_path) 로드
            2. 모든 paragraph.text 추출
            3. 모든 table cell.text 추출
            4. 결합 후 반환
            5. 실패 시: docx2txt.process() fallback
        """
    
    def _parse_doc(self, file_path: Path) -> str:
        """
        DOC 파일 파싱 (Windows only)
        
        Implementation:
            1. win32com.client.Dispatch("Word.Application")
            2. word.Visible = False
            3. doc = word.Documents.Open(file_path)
            4. text = doc.Content.Text
            5. doc.Close(False)
            6. word.Quit()
            7. 실패 시: 빈 문자열 + 경고
        """
    
    def _parse_xlsx(self, file_path: Path) -> str:
        """
        XLSX/XLS 파일 파싱
        
        Implementation:
            1. openpyxl.load_workbook(file_path, data_only=True)
            2. 각 시트별 순회
            3. 시트명 추가
            4. 모든 행의 셀 값을 " | "로 결합
            5. 모든 시트 결합 후 반환
        """
    
    def _parse_pdf(self, file_path: Path) -> str:
        """
        PDF 파일 파싱
        
        Implementation:
            1. PdfReader(file_path)
            2. 각 페이지별 순회
            3. page.extract_text()
            4. 페이지 구분자 추가
            5. 모든 페이지 결합 후 반환
        """
```

### 5.3 src/vector_store.py

#### 클래스: VectorStoreManager

```python
class VectorStoreManager:
    """벡터 스토어 관리 클래스"""
    
    def __init__(
        self,
        persist_directory: str = "./chroma_db",
        embedding_model: str = "text-embedding-3-small",
        chunk_size: int = 1000,
        chunk_overlap: int = 200
    ):
        """
        Args:
            persist_directory: ChromaDB 저장 디렉토리
            embedding_model: OpenAI 임베딩 모델
            chunk_size: 텍스트 청크 크기
            chunk_overlap: 청크 간 중복 크기
            
        Attributes:
            self.embeddings: OpenAIEmbeddings
            self.text_splitter: RecursiveCharacterTextSplitter
            self.vectorstore: Optional[Chroma]
        """
    
    def create_vectorstore(
        self, 
        documents: List[Document], 
        force_recreate: bool = False
    ) -> Chroma:
        """
        문서로부터 벡터 스토어를 생성합니다.
        
        Args:
            documents: 문서 리스트
            force_recreate: 기존 벡터 스토어를 강제로 재생성할지 여부
        
        Returns:
            Chroma 벡터 스토어
            
        Implementation:
            1. force_recreate=False이고 기존 DB 있으면 load_vectorstore()
            2. text_splitter.split_documents(documents)로 청킹
            3. Chroma.from_documents(
                   documents=chunks,
                   embedding=self.embeddings,
                   persist_directory=self.persist_directory,
                   collection_name="niceinfo_rules"
               )
            4. self.vectorstore에 저장
            5. 반환
        """
    
    def load_vectorstore(self) -> Chroma:
        """
        기존 벡터 스토어를 로드합니다.
        
        Returns:
            Chroma 벡터 스토어
            
        Raises:
            ValueError: 벡터 스토어가 존재하지 않는 경우
            
        Implementation:
            1. 디렉토리 존재 확인
            2. Chroma(
                   persist_directory=self.persist_directory,
                   embedding_function=self.embeddings,
                   collection_name="niceinfo_rules"
               )
            3. self.vectorstore에 저장
            4. 반환
        """
    
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
            
        Implementation:
            1. vectorstore 존재 확인
            2. vectorstore.similarity_search_with_score(
                   query=query,
                   k=k,
                   filter=filter_dict
               )
            3. 반환
        """
    
    def get_retriever(self, search_kwargs: Optional[dict] = None):
        """
        Retriever 객체를 반환합니다.
        
        Args:
            search_kwargs: 검색 옵션 (기본: {"k": 4})
        
        Returns:
            VectorStoreRetriever
            
        Implementation:
            1. vectorstore 존재 확인
            2. vectorstore.as_retriever(search_kwargs=search_kwargs)
            3. 반환
        """
    
    def delete_vectorstore(self):
        """
        벡터 스토어를 삭제합니다.
        
        Implementation:
            1. 디렉토리 존재 확인
            2. shutil.rmtree(self.persist_directory)
            3. self.vectorstore = None
            4. 로그
        """
```

### 5.4 src/rag_chain.py

#### 클래스: RAGChain

```python
class RAGChain:
    """RAG 체인 클래스"""
    
    def __init__(
        self,
        vector_store_manager: VectorStoreManager,
        model_name: str = "gpt-4-turbo-preview",
        temperature: float = 0,
        similarity_threshold: float = 0.5,
        top_k: int = 4
    ):
        """
        Args:
            vector_store_manager: 벡터 스토어 관리자
            model_name: OpenAI 모델 이름
            temperature: 생성 온도
            similarity_threshold: 유사도 임계값
            top_k: 검색할 문서 수
            
        Attributes:
            self.llm: ChatOpenAI
            self.prompt: PromptTemplate
            self.chain: RetrievalQA
        """
    
    def _initialize_chain(self):
        """
        체인을 초기화합니다.
        
        Implementation:
            1. vectorstore = vs_manager.get_vectorstore()
            2. retriever = vs_manager.get_retriever({"k": top_k})
            3. self.chain = RetrievalQA.from_chain_type(
                   llm=self.llm,
                   chain_type="stuff",
                   retriever=retriever,
                   return_source_documents=True,
                   chain_type_kwargs={"prompt": self.prompt}
               )
        """
    
    def query(self, question: str) -> Dict[str, any]:
        """
        질문에 대한 답변을 생성합니다.
        
        Args:
            question: 사용자 질문
        
        Returns:
            {
                "answer": str,
                "sources": List[dict],
                "is_out_of_scope": bool,
                "confidence": float
            }
            
        Implementation:
            1. vs_manager.similarity_search(question, k=top_k)
            2. 결과 없음 → OUT_OF_SCOPE
            3. best_score > threshold → OUT_OF_SCOPE
            4. self.chain({"query": question})
            5. source_documents 정리
            6. 응답 딕셔너리 구성 후 반환
        """
```

#### 클래스: ConversationalRAGChain

```python
class ConversationalRAGChain(RAGChain):
    """대화형 RAG 체인 클래스"""
    
    def __init__(self, *args, **kwargs):
        """
        Attributes:
            self.conversation_history: List[Dict[str, str]]
        """
    
    def query_with_history(self, question: str) -> Dict[str, any]:
        """
        대화 히스토리를 고려하여 답변합니다.
        
        Args:
            question: 사용자 질문
        
        Returns:
            query()와 동일
            
        Implementation:
            1. 히스토리가 있으면 최근 2개 추출
            2. "이전 질문: ... 이전 답변: ... 현재 질문: ..."로 컨텍스트 구성
            3. self.query(context_question) 호출
            4. 결과를 conversation_history에 추가
            5. 반환
        """
    
    def clear_history(self):
        """
        대화 히스토리를 초기화합니다.
        
        Implementation:
            self.conversation_history = []
        """
```

### 5.5 app.py

#### 함수: initialize_session_state()

```python
def initialize_session_state():
    """
    세션 상태 초기화
    
    Implementation:
        if key not in st.session_state:
            st.session_state[key] = default_value
            
        Keys:
            - messages: []
            - rag_chain: None
            - vectorstore_loaded: False
            - show_sources: True
    """
```

#### 함수: initialize_rag_system()

```python
def initialize_rag_system() -> bool:
    """
    RAG 시스템 초기화
    
    Returns:
        성공 여부 (bool)
        
    Implementation:
        1. load_dotenv()
        2. OPENAI_API_KEY 확인 → 없으면 에러
        3. VectorStoreManager 초기화
        4. chroma_db 존재 확인
           - 있으면: load_vectorstore()
           - 없으면: 문서 로드 → create_vectorstore()
        5. ConversationalRAGChain 초기화
        6. st.session_state.rag_chain에 저장
        7. 성공 시 True, 실패 시 False
    """
```

#### 함수: display_message()

```python
def display_message(role: str, content: str, sources: list = None):
    """
    메시지 표시
    
    Args:
        role: "user" 또는 "assistant"
        content: 메시지 내용
        sources: 참고 문서 리스트 (선택)
        
    Implementation:
        1. role에 따라 다른 스타일 적용
        2. st.markdown()으로 HTML 렌더링
        3. sources가 있고 show_sources=True면
           st.expander()로 출처 표시
    """
```

#### 함수: sidebar()

```python
def sidebar():
    """
    사이드바 UI
    
    Implementation:
        with st.sidebar:
            1. 설정 섹션
               - show_sources 체크박스
            2. 버튼 섹션
               - 대화 내역 지우기 → st.rerun()
               - 문서 재인덱싱 → delete → rerun
            3. 사용 안내 (정적 텍스트)
            4. 시스템 상태 표시
    """
```

#### 함수: main()

```python
def main():
    """
    메인 함수
    
    Implementation:
        1. initialize_session_state()
        2. 헤더 표시
        3. sidebar()
        4. if rag_chain is None:
               initialize_rag_system()
        5. 경고 메시지
        6. 대화 내역 표시 (messages)
        7. st.chat_input() 처리
           - 메시지 추가
           - rag_chain.query_with_history()
           - 응답 표시
           - 메시지 저장
    """
```

### 5.6 setup_db.py

```python
def main():
    """
    벡터 데이터베이스 초기 설정
    
    Implementation:
        1. 환경 변수 로드
        2. API 키 확인
        3. reference 폴더 확인
        4. 기존 chroma_db 확인 → 삭제 확인
        5. DocumentLoader로 문서 로드
        6. 카테고리별 통계 출력
        7. VectorStoreManager로 벡터 DB 생성
        8. 테스트 검색 수행
        9. 완료 메시지
    """
```

### 5.7 check_system.py

```python
def check_python_version() -> bool:
    """Python 버전 확인 (≥3.8)"""

def check_dependencies() -> bool:
    """의존성 패키지 확인"""

def check_env_file() -> bool:
    """.env 파일 및 API 키 확인"""

def check_reference_folder() -> bool:
    """reference 폴더 및 문서 파일 확인"""

def check_vector_db() -> bool:
    """벡터 DB 존재 확인"""

def check_windows_specific() -> bool:
    """Windows 환경 (win32com) 확인"""

def main():
    """
    모든 체크 수행 후 결과 요약 출력
    
    Implementation:
        1. 각 체크 함수 실행
        2. 결과 딕셔너리에 저장
        3. 요약 출력
        4. 통과 시: 다음 단계 안내
        5. 실패 시: 해결 방법 안내
    """
```

### 5.8 run.py

```python
def check_prerequisites() -> List[str]:
    """
    사전 요구사항 확인
    
    Returns:
        에러 메시지 리스트 (빈 리스트면 성공)
        
    Checks:
        - Python 버전
        - .env 파일
        - reference 폴더
        - streamlit 패키지
    """

def main():
    """
    챗봇 실행 헬퍼
    
    Implementation:
        1. check_prerequisites()
        2. 에러 있으면 출력 후 종료
        3. subprocess.run([python, "-m", "streamlit", "run", "app.py"])
        4. KeyboardInterrupt 처리
    """
```

---

## 6. 데이터 명세

### 6.1 문서 메타데이터

```python
DocumentMetadata = {
    'source': str,          # 예: "D:/project/.../reference/1)_조직_11/조직1)_정관.doc"
    'filename': str,        # 예: "조직1)_정관.doc"
    'category': str,        # 예: "조직"
    'file_type': str        # 예: ".doc"
}
```

### 6.2 LangChain Document

```python
from langchain.schema import Document

Document(
    page_content: str,              # 문서 텍스트 내용
    metadata: DocumentMetadata      # 메타데이터
)
```

### 6.3 청크 데이터

```python
Chunk = Document(
    page_content: str,              # 청크 텍스트 (최대 1000자)
    metadata: DocumentMetadata      # 원본 문서 메타데이터 (동일)
)
```

### 6.4 벡터 데이터

```python
VectorData = {
    'id': str,                      # ChromaDB 자동 생성
    'embedding': List[float],       # 1536차원 벡터
    'document': str,                # 청크 텍스트
    'metadata': DocumentMetadata    # 메타데이터
}
```

### 6.5 검색 결과

```python
SearchResult = Tuple[Document, float]
# (문서, 거리 점수)
# 거리: L2 distance (낮을수록 유사)
```

### 6.6 RAG 응답

```python
RAGResponse = {
    'answer': str,                  # 생성된 답변
    'sources': List[SourceInfo],    # 참고 문서 목록
    'is_out_of_scope': bool,        # 범위 밖 여부
    'confidence': float             # 신뢰도 (0-1)
}

SourceInfo = {
    'filename': str,                # 파일명
    'category': str,                # 카테고리
    'content_preview': str          # 내용 미리보기 (200자)
}
```

### 6.7 대화 메시지

```python
Message = {
    'role': str,                    # "user" 또는 "assistant"
    'content': str,                 # 메시지 내용
    'sources': List[SourceInfo],    # 참고 문서 (assistant만)
    'is_out_of_scope': bool,        # 범위 밖 여부 (assistant만)
    'confidence': float             # 신뢰도 (assistant만)
}
```

### 6.8 대화 히스토리

```python
ConversationHistory = List[ConversationTurn]

ConversationTurn = {
    'question': str,                # 사용자 질문
    'answer': str                   # AI 답변
}
```

---

## 7. 인터페이스 명세

### 7.1 환경 변수

```bash
# .env 파일

# 필수
OPENAI_API_KEY=sk-...              # OpenAI API 키

# 선택 (기본값 있음)
OPENAI_MODEL=gpt-4-turbo-preview   # 사용할 GPT 모델
EMBEDDING_MODEL=text-embedding-3-small  # 임베딩 모델
```

### 7.2 OpenAI API

#### Embeddings API

```python
# Request
POST https://api.openai.com/v1/embeddings
{
    "model": "text-embedding-3-small",
    "input": "텍스트 내용"
}

# Response
{
    "data": [
        {
            "embedding": [0.1, 0.2, ...],  # 1536차원
            "index": 0
        }
    ],
    "model": "text-embedding-3-small",
    "usage": {...}
}
```

#### Chat Completions API

```python
# Request
POST https://api.openai.com/v1/chat/completions
{
    "model": "gpt-4-turbo-preview",
    "messages": [
        {"role": "system", "content": "시스템 프롬프트"},
        {"role": "user", "content": "사용자 질문"}
    ],
    "temperature": 0
}

# Response
{
    "choices": [
        {
            "message": {
                "role": "assistant",
                "content": "AI 답변"
            },
            "finish_reason": "stop"
        }
    ],
    "usage": {...}
}
```

### 7.3 ChromaDB API

#### Create Collection

```python
collection = client.create_collection(
    name="niceinfo_rules",
    metadata={"hnsw:space": "l2"}
)
```

#### Add Documents

```python
collection.add(
    documents=["텍스트1", "텍스트2", ...],
    embeddings=[[0.1, 0.2, ...], [0.3, 0.4, ...], ...],
    metadatas=[{...}, {...}, ...],
    ids=["id1", "id2", ...]
)
```

#### Query

```python
results = collection.query(
    query_embeddings=[[0.1, 0.2, ...]],
    n_results=4,
    where={"category": "조직"}  # 선택
)

# Returns
{
    "ids": [["id1", "id2", ...]],
    "distances": [[0.5, 0.7, ...]],
    "documents": [["텍스트1", "텍스트2", ...]],
    "metadatas": [[{...}, {...}, ...]]
}
```

### 7.4 Streamlit Session State API

```python
# 읽기
value = st.session_state.key_name
value = st.session_state["key_name"]

# 쓰기
st.session_state.key_name = value
st.session_state["key_name"] = value

# 확인
if "key_name" in st.session_state:
    ...

# 삭제
del st.session_state["key_name"]
```

### 7.5 파일 시스템 인터페이스

#### 입력 디렉토리

```
./reference/
├── [NICE평가정보]_내규 정보 모음/
│   ├── 1)_조직_11/
│   │   ├── 조직1)_정관.doc
│   │   ├── 조직2)_내규관리규정.doc
│   │   └── ...
│   ├── 2)_인사_21/
│   ├── 3)_복지_12/
│   └── ...
└── ...
```

#### 출력 디렉토리

```
./chroma_db/
├── chroma.sqlite3           # SQLite 데이터베이스
└── [기타 ChromaDB 파일들]
```

---

## 8. 배포 명세

### 8.1 시스템 요구사항

#### 하드웨어

- **CPU**: 2+ 코어 (권장: 4+ 코어)
- **RAM**: 4GB+ (권장: 8GB+)
- **디스크**: 10GB+ 여유 공간
  - 벡터 DB: 문서 크기의 2-3배
  - Python 환경: 1-2GB

#### 소프트웨어

- **OS**: Windows 10/11, Linux, macOS
- **Python**: 3.8 이상 (권장: 3.10+)
- **Python 패키지**: requirements.txt 참조
- **Microsoft Word**: .doc 파일 처리 시 필요 (Windows only)

### 8.2 설치 절차

#### 1단계: 환경 준비

```bash
# Python 버전 확인
python --version  # 3.8 이상

# 가상환경 생성 (권장)
python -m venv venv

# 가상환경 활성화
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

#### 2단계: 의존성 설치

```bash
# requirements.txt 설치
pip install -r requirements.txt

# Windows에서 .doc 파일 지원
pip install pywin32
```

#### 3단계: 환경 설정

```bash
# .env 파일 생성
copy env_template.txt .env  # Windows
cp env_template.txt .env    # Linux/Mac

# .env 파일 편집
# OPENAI_API_KEY=your-actual-api-key
```

#### 4단계: 문서 배치

```bash
# reference 폴더에 내규 문서 배치
./reference/
  └── [문서 파일들]
```

#### 5단계: 시스템 체크

```bash
python check_system.py
```

#### 6단계: 벡터 DB 생성

```bash
# 선택 A: 자동 생성 (앱 실행 시)
streamlit run app.py

# 선택 B: 수동 생성
python setup_db.py
```

### 8.3 실행 방법

#### 로컬 실행

```bash
# 방법 1: 헬퍼 스크립트
python run.py

# 방법 2: Streamlit 직접 실행
streamlit run app.py

# 방법 3: Windows 배치 파일
start_chatbot.bat
```

#### 네트워크 접근 허용

```bash
# 같은 네트워크의 다른 기기에서 접근
streamlit run app.py --server.address=0.0.0.0 --server.port=8501
```

### 8.4 프로덕션 배포

#### Streamlit Cloud

```bash
# 1. GitHub 저장소 생성
# 2. 코드 푸시
# 3. Streamlit Cloud 연결
# 4. Secrets에 OPENAI_API_KEY 설정
# 5. 배포
```

#### Docker 배포

```dockerfile
# Dockerfile (참고용)
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0"]
```

```bash
# 빌드 및 실행
docker build -t niceinfo-chatbot .
docker run -p 8501:8501 -v ./reference:/app/reference -v ./chroma_db:/app/chroma_db niceinfo-chatbot
```

### 8.5 유지보수

#### 문서 업데이트

```bash
# 1. 새 문서를 ./reference에 추가
# 2. 재인덱싱
python setup_db.py
# 또는 웹 UI에서 "문서 재인덱싱" 버튼
```

#### 로그 관리

```python
# 로깅 레벨 변경 (코드 수정)
import logging
logging.basicConfig(level=logging.DEBUG)
```

#### 백업

```bash
# 백업 대상
./chroma_db/         # 벡터 DB
./reference/         # 원본 문서
.env                 # 환경 변수
```

---

## 9. 테스트 요구사항

### 9.1 단위 테스트

#### 9.1.1 utils.py

```python
def test_get_all_documents():
    """문서 탐색 테스트"""
    # 준비: 테스트 디렉토리 생성
    # 실행: get_all_documents()
    # 검증:
    #   - 지원 형식만 반환
    #   - .zip 파일 제외
    #   - 정렬된 결과

def test_extract_category_from_path():
    """카테고리 추출 테스트"""
    # 케이스:
    #   - "1)_조직_11" → "조직"
    #   - "2)_인사_21" → "인사"
    #   - 일반 폴더 → "기타"

def test_clean_text():
    """텍스트 정리 테스트"""
    # 케이스:
    #   - 과도한 공백
    #   - 연속 빈 줄
```

#### 9.1.2 document_loader.py

```python
def test_parse_docx():
    """DOCX 파싱 테스트"""
    # 준비: 샘플 DOCX 파일
    # 실행: _parse_docx()
    # 검증: 텍스트 추출 성공

def test_parse_xlsx():
    """XLSX 파싱 테스트"""
    # 준비: 샘플 XLSX 파일
    # 실행: _parse_xlsx()
    # 검증: 모든 시트 추출

def test_load_documents():
    """문서 로딩 통합 테스트"""
    # 검증:
    #   - 메타데이터 올바름
    #   - 빈 문서 제외
    #   - 에러 핸들링
```

#### 9.1.3 vector_store.py

```python
def test_create_vectorstore():
    """벡터 스토어 생성 테스트"""
    # 준비: 샘플 문서
    # 실행: create_vectorstore()
    # 검증:
    #   - 디렉토리 생성
    #   - 파일 존재

def test_similarity_search():
    """유사도 검색 테스트"""
    # 준비: 벡터 스토어 생성
    # 실행: similarity_search()
    # 검증:
    #   - k개 결과 반환
    #   - 점수 포함
```

#### 9.1.4 rag_chain.py

```python
def test_query_in_scope():
    """범위 내 질문 테스트"""
    # 케이스: "직원 복무 규정"
    # 검증:
    #   - is_out_of_scope = False
    #   - answer 존재
    #   - sources 존재

def test_query_out_of_scope():
    """범위 밖 질문 테스트"""
    # 케이스: "날씨"
    # 검증:
    #   - is_out_of_scope = True
    #   - 범위 밖 메시지

def test_conversation_history():
    """대화 히스토리 테스트"""
    # 실행: 여러 번 query_with_history()
    # 검증:
    #   - 히스토리 누적
    #   - clear_history() 동작
```

### 9.2 통합 테스트

#### 9.2.1 전체 플로우

```python
def test_end_to_end():
    """전체 플로우 테스트"""
    # 1. 문서 로드
    # 2. 벡터 스토어 생성
    # 3. RAG 체인 초기화
    # 4. 질문 → 답변
    # 검증: 전체 과정 성공
```

#### 9.2.2 UI 테스트

```python
def test_streamlit_app():
    """Streamlit 앱 테스트"""
    # 도구: pytest + streamlit testing
    # 검증:
    #   - 페이지 로드
    #   - 세션 상태
    #   - 버튼 동작
```

### 9.3 성능 테스트

```python
def test_query_performance():
    """쿼리 성능 테스트"""
    # 측정:
    #   - 검색 시간 < 1초
    #   - 전체 응답 < 10초
    # 반복: 10회 평균

def test_load_performance():
    """로딩 성능 테스트"""
    # 측정:
    #   - 100개 문서 로딩 시간
    #   - 벡터화 시간
```

### 9.4 품질 테스트

```python
def test_answer_quality():
    """답변 품질 테스트"""
    # 질문-답변 쌍 준비
    # 실행: query()
    # 검증:
    #   - 관련성 (수동 또는 LLM 평가)
    #   - 출처 정확성

def test_scope_detection():
    """범위 판단 정확도 테스트"""
    # 범위 내 질문 10개
    # 범위 밖 질문 10개
    # 검증: 정확도 > 90%
```

### 9.5 테스트 실행

```bash
# 단위 테스트
pytest tests/test_utils.py
pytest tests/test_document_loader.py
pytest tests/test_vector_store.py
pytest tests/test_rag_chain.py

# 통합 테스트
pytest tests/test_integration.py

# 전체 테스트
pytest

# 커버리지
pytest --cov=src --cov-report=html
```

---

## 10. 제약사항 및 가정

### 10.1 제약사항

1. **OpenAI API 의존**
   - 인터넷 연결 필수
   - API 비용 발생
   - API 제한에 종속

2. **문서 형식**
   - 지원: .doc, .docx, .xlsx, .pdf
   - 미지원: 이미지, 차트 (텍스트만)

3. **Windows 특화**
   - .doc 파일은 Windows + MS Word 필요
   - 다른 OS에서는 .doc 건너뛰기

4. **단일 사용자**
   - Streamlit 기본 설정은 단일 프로세스
   - 다중 사용자는 별도 배포 필요

5. **보안**
   - 문서 내용이 OpenAI로 전송됨
   - 민감 정보 주의

### 10.2 가정

1. **문서 구조**
   - reference 폴더 구조: `N)_카테고리_X/`
   - 파일명에 의미 있는 정보 포함

2. **문서 품질**
   - 텍스트 추출 가능
   - 한글 인코딩 정상

3. **API 가용성**
   - OpenAI API 정상 작동
   - 합리적인 응답 시간 (<10초)

4. **사용자 행동**
   - 내규 관련 질문
   - 한국어 사용
   - 정상적인 사용 (스팸 없음)

---

## 11. 용어집

| 용어 | 설명 |
|------|------|
| RAG | Retrieval-Augmented Generation, 검색 증강 생성 |
| LLM | Large Language Model, 대형 언어 모델 |
| 임베딩 | 텍스트를 벡터로 변환하는 과정 |
| 벡터 DB | 벡터 데이터를 저장하고 검색하는 데이터베이스 |
| 청킹 | 긴 텍스트를 작은 단위로 분할 |
| 유사도 검색 | 벡터 간 거리를 계산하여 유사한 문서 찾기 |
| 프롬프트 | LLM에 전달하는 입력 텍스트 |
| 컨텍스트 | 질문과 함께 제공되는 관련 문서 |
| 범위 밖 | 제공된 문서에 없는 내용에 대한 질문 |
| 세션 상태 | Streamlit에서 페이지 새로고침 간 유지되는 상태 |

---

## 12. 참고 자료

### 12.1 공식 문서

- **LangChain**: https://python.langchain.com/docs/
- **OpenAI API**: https://platform.openai.com/docs/
- **ChromaDB**: https://docs.trychroma.com/
- **Streamlit**: https://docs.streamlit.io/

### 12.2 패키지 문서

- **python-docx**: https://python-docx.readthedocs.io/
- **openpyxl**: https://openpyxl.readthedocs.io/
- **PyPDF2**: https://pypdf2.readthedocs.io/

### 12.3 관련 개념

- **RAG Pattern**: https://arxiv.org/abs/2005.11401
- **Semantic Search**: https://en.wikipedia.org/wiki/Semantic_search
- **Vector Embeddings**: https://platform.openai.com/docs/guides/embeddings

---

## 13. 변경 이력

| 버전 | 날짜 | 작성자 | 변경 내용 |
|------|------|--------|-----------|
| 1.0 | 2025-11-11 | AI Team | 초기 명세서 작성 |

---

## 14. 승인

| 역할 | 이름 | 서명 | 날짜 |
|------|------|------|------|
| 작성자 | AI Development Team | | 2025-11-11 |
| 검토자 | | | |
| 승인자 | | | |

---

**문서 끝**

이 명세서는 NICE평가정보 내규 챗봇 시스템의 완전한 재구현을 위한 모든 정보를 포함합니다.

