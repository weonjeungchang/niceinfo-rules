"""유틸리티 함수 모음"""

import os
from pathlib import Path
from typing import List


def get_all_documents(root_dir: str, exclude_extensions: List[str] = None) -> List[Path]:
    """
    지정된 디렉토리에서 모든 문서 파일을 재귀적으로 찾습니다.
    
    Args:
        root_dir: 검색할 루트 디렉토리
        exclude_extensions: 제외할 파일 확장자 리스트 (예: ['.zip'])
    
    Returns:
        파일 경로 리스트
    """
    if exclude_extensions is None:
        exclude_extensions = ['.zip']
    
    root_path = Path(root_dir)
    if not root_path.exists():
        raise ValueError(f"디렉토리가 존재하지 않습니다: {root_dir}")
    
    # 지원하는 문서 형식
    supported_extensions = ['.doc', '.docx', '.xlsx', '.xls', '.pdf']
    
    documents = []
    for file_path in root_path.rglob('*'):
        if file_path.is_file():
            ext = file_path.suffix.lower()
            # 지원하는 확장자이고 제외 목록에 없으면 추가
            if ext in supported_extensions and ext not in exclude_extensions:
                documents.append(file_path)
    
    return sorted(documents)


def extract_category_from_path(file_path: Path, root_dir: str) -> str:
    """
    파일 경로에서 카테고리를 추출합니다.
    
    Args:
        file_path: 파일 경로
        root_dir: 루트 디렉토리
    
    Returns:
        카테고리 문자열
    """
    try:
        relative_path = file_path.relative_to(root_dir)
        parts = relative_path.parts
        
        # 첫 번째 폴더명에서 카테고리 추출
        if len(parts) > 1:
            # 예: "1)_조직_11" -> "조직"
            folder_name = parts[0]
            if '_' in folder_name:
                category = folder_name.split('_')[1] if len(folder_name.split('_')) > 1 else folder_name
                return category
            return folder_name
        
        return "기타"
    except:
        return "기타"


def clean_text(text: str) -> str:
    """
    텍스트를 정리합니다.
    
    Args:
        text: 원본 텍스트
    
    Returns:
        정리된 텍스트
    """
    if not text:
        return ""
    
    # 과도한 공백 제거
    lines = [line.strip() for line in text.split('\n')]
    # 빈 줄이 3개 이상 연속되는 경우 2개로 축소
    cleaned_lines = []
    empty_count = 0
    
    for line in lines:
        if not line:
            empty_count += 1
            if empty_count <= 2:
                cleaned_lines.append(line)
        else:
            empty_count = 0
            cleaned_lines.append(line)
    
    return '\n'.join(cleaned_lines)

