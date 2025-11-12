# NICE평가정보 내규 챗봇 📚

NICE평가정보의 내규 및 규정 문서를 기반으로 답변하는 AI 챗봇입니다. RAG (Retrieval-Augmented Generation) 기술을 활용하여 정확하고 신뢰할 수 있는 답변을 제공합니다.

## 주요 기능 ✨

- 📄 **문서 기반 답변**: `./reference` 폴더 내의 모든 내규 문서를 분석하여 답변
- 🔍 **의미론적 검색**: 질문의 의도를 파악하여 관련 문서를 정확하게 검색
- 🎯 **범위 제한**: 제공된 문서 범위 외의 질문에는 명확히 답변 불가 안내
- 💬 **대화형 인터페이스**: Streamlit 기반의 사용하기 쉬운 웹 UI
- 📚 **출처 표시**: 답변의 근거가 된 문서 정보 제공
- 🔄 **문서 재인덱싱**: 문서 업데이트 시 쉽게 재인덱싱 가능

## 기술 스택 🛠️

- **Python 3.8+**
- **LangChain**: RAG 파이프라인 구성
- **OpenAI API**: GPT-4 및 임베딩 모델
- **ChromaDB**: 벡터 데이터베이스
- **Streamlit**: 웹 UI 프레임워크
- **Document Parsers**: python-docx, openpyxl, PyPDF2

## 설치 방법 🚀

### 1. 저장소 클론

```bash
git clone <repository-url>
cd niceinfo-rules-chatbot
```

### 2. 가상환경 생성 (권장)

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 3. 의존성 설치

```bash
pip install -r requirements.txt
```

### 4. 환경 변수 설정

`env_template.txt` 파일을 참고하여 `.env` 파일을 생성하고 OpenAI API 키를 설정합니다:

```bash
# .env 파일 생성
copy env_template.txt .env  # Windows
cp env_template.txt .env    # Linux/Mac
```

`.env` 파일을 열어 API 키를 입력:

```
OPENAI_API_KEY=your-actual-api-key-here
```

OpenAI API 키는 https://platform.openai.com/api-keys 에서 발급받을 수 있습니다.

### 5. 문서 준비

`./reference` 폴더에 내규 문서가 있는지 확인합니다. 지원되는 형식:
- `.doc`, `.docx` (Word 문서)
- `.xlsx`, `.xls` (Excel 문서)
- `.pdf` (PDF 문서)

**주의**: `.zip` 파일은 자동으로 제외됩니다.

## 사용 방법 💡

### 1. 챗봇 실행

```bash
streamlit run app.py
```

브라우저가 자동으로 열리며 `http://localhost:8501`에서 챗봇에 접속할 수 있습니다.

### 2. 첫 실행 시

- 처음 실행 시 모든 문서를 로드하고 벡터화하는 과정이 진행됩니다
- 문서 수에 따라 5-10분 정도 소요될 수 있습니다
- 벡터 데이터베이스는 `./chroma_db` 폴더에 저장되며, 다음 실행 시 재사용됩니다

### 3. 챗봇 사용

1. 텍스트 입력창에 질문을 입력합니다
2. Enter 키를 누르거나 전송 버튼을 클릭합니다
3. AI 어시스턴트가 문서를 검색하여 답변을 생성합니다
4. 필요시 "참고 문서 보기"를 클릭하여 출처를 확인합니다

### 4. 주요 기능

#### 대화 내역 지우기
- 사이드바의 "🗑️ 대화 내역 지우기" 버튼 클릭

#### 문서 재인덱싱
- 문서가 업데이트된 경우 사이드바의 "🔄 문서 재인덱싱" 버튼 클릭
- 기존 벡터 DB가 삭제되고 새로 생성됩니다

#### 참고 문서 표시/숨김
- 사이드바의 "참고 문서 표시" 체크박스로 제어

## 프로젝트 구조 📁

```
niceinfo-rules-chatbot/
├── app.py                      # Streamlit 메인 애플리케이션
├── requirements.txt            # Python 의존성
├── .env                        # 환경 변수 (생성 필요)
├── env_template.txt            # 환경 변수 템플릿
├── .gitignore                  # Git 제외 파일
├── README.md                   # 프로젝트 문서
│
├── src/                        # 소스 코드
│   ├── __init__.py
│   ├── document_loader.py      # 문서 로딩 및 파싱
│   ├── vector_store.py         # ChromaDB 벡터 스토어 관리
│   ├── rag_chain.py            # RAG 체인 구성
│   └── utils.py                # 유틸리티 함수
│
├── reference/                  # 내규 문서 폴더
│   └── [NICE평가정보]_내규 정보 모음/
│
└── chroma_db/                  # 벡터 데이터베이스 (자동 생성)
```

## 지원 문서 카테고리 📋

챗봇은 다음 카테고리의 내규에 대해 답변합니다:

- 📋 **조직**: 정관, 내규관리규정, 이사회운영규정, 직제규정 등
- 👥 **인사**: 인사규정, 복무규정, 급여규정, 취업규칙 등
- 💰 **복지**: 복지규정, 경조사지원, 건강검진 등
- 🔍 **감사**: 감사규정, 윤리강령, 내부통제 등
- 💼 **업무**: 각종 업무 관련 지침 및 규정
- 💻 **IT**: 정보시스템 관련 규정 및 지침
- 🏢 **기업평가**: 평가 관련 규정 및 지침
- 🏦 **금융소비자보호**: 금융소비자 보호 관련 규정

## 개발 및 테스트 🔧

### 개별 모듈 테스트

각 모듈은 독립적으로 테스트할 수 있습니다:

```bash
# 문서 로더 테스트
python -m src.document_loader

# 벡터 스토어 테스트
python -m src.vector_store

# RAG 체인 테스트
python -m src.rag_chain
```

### 로깅

애플리케이션은 INFO 레벨의 로깅을 제공합니다. 자세한 로그를 보려면:

```python
# 코드에서 로깅 레벨 변경
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 문제 해결 🔧

### 1. "OPENAI_API_KEY가 설정되지 않았습니다" 오류

- `.env` 파일이 존재하고 API 키가 올바르게 설정되어 있는지 확인
- 파일 이름이 정확히 `.env`인지 확인 (`.env.txt`가 아님)

### 2. 문서 로딩 실패

- `./reference` 폴더에 문서가 있는지 확인
- 문서 형식이 지원되는지 확인 (.doc, .docx, .xlsx, .pdf)
- Windows에서 `.doc` 파일 처리를 위해 Microsoft Word가 설치되어 있는지 확인

### 3. "벡터 스토어를 로드할 수 없습니다" 오류

- `./chroma_db` 폴더를 삭제하고 재실행
- 또는 사이드바에서 "문서 재인덱싱" 버튼 클릭

### 4. 느린 응답 속도

- 첫 번째 질문은 벡터 DB 로드로 인해 느릴 수 있습니다
- OpenAI API 호출로 인해 2-5초의 지연이 정상입니다
- 네트워크 연결 상태를 확인하세요

### 5. 메모리 부족 오류

- 문서가 너무 많은 경우 청크 크기를 줄이거나 일부 문서만 로드하도록 수정
- `src/vector_store.py`에서 `chunk_size`를 조정

## 주의사항 ⚠️

1. **데이터 보안**: 민감한 내규 문서는 OpenAI API로 전송됩니다. 보안 정책을 확인하세요.
2. **API 비용**: OpenAI API 사용에 따른 비용이 발생합니다.
3. **정확도**: AI가 생성한 답변이므로 중요한 결정에는 원본 문서를 직접 확인하세요.
4. **문서 업데이트**: 문서가 변경되면 반드시 재인덱싱을 수행하세요.

## 라이선스 📄

이 프로젝트는 NICE평가정보 내부용으로 개발되었습니다.

## 지원 💬

문제가 발생하거나 기능 개선 제안이 있는 경우 이슈를 등록해주세요.

---

**Powered by OpenAI, LangChain, and ChromaDB** 🚀

