@echo off
chcp 65001 >nul
echo ============================================
echo     股票研究系统 - 一键启动
echo ============================================
echo.

:: 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到Python，请先安装Python 3.9+
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

:: 检查依赖是否安装
python -c "import streamlit" >nul 2>&1
if errorlevel 1 (
    echo [提示] 正在安装依赖，请稍候...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo [错误] 依赖安装失败
        pause
        exit /b 1
    )
)

:: 检查API Key
findstr /C "sk-your-api-key-here" .env >nul 2>&1
if not errorlevel 1 (
    echo.
    echo ============================================
    echo [重要] 请先配置您的OpenAI API Key！
    echo ============================================
    echo 请用记事本打开 .env 文件
    echo 将 OPENAI_API_KEY=sk-your-api-key-here
    echo 改成您的真实API Key
    echo 例如: OPENAI_API_KEY=sk-xxxxxxx
    echo.
    echo 配置完成后，重新运行此脚本
    echo ============================================
    pause
    exit /b 1
)

echo [启动中] 正在启动股票研究系统...
echo [提示] 按 Ctrl+C 可以停止系统
echo.
streamlit run app.py --server.headless true --browser.gatherUsageStats false
pause
