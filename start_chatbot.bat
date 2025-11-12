@echo off
chcp 65001 >nul
echo ====================================
echo NICE평가정보 내규 챗봇 시작
echo ====================================
echo.

REM 가상환경 활성화 (있는 경우)
if exist "venv\Scripts\activate.bat" (
    echo 가상환경 활성화 중...
    call venv\Scripts\activate.bat
)

REM Streamlit 실행
echo 챗봇을 시작합니다...
echo 브라우저가 자동으로 열립니다.
echo 종료하려면 Ctrl+C를 누르세요.
echo.

streamlit run app.py

pause

