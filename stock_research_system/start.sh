#!/bin/bash

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "============================================"
echo "    股票研究系统 - 一键启动"
echo "============================================"
echo ""

# 检查Python是否安装
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}[错误] 未检测到Python，请先安装Python 3.9+${NC}"
    echo "下载地址: https://www.python.org/downloads/"
    read -p "按回车键退出..."
    exit 1
fi

# 检查依赖是否安装
if ! python3 -c "import streamlit" &> /dev/null; then
    echo -e "${YELLOW}[提示] 正在安装依赖，请稍候...${NC}"
    pip3 install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo -e "${RED}[错误] 依赖安装失败${NC}"
        read -p "按回车键退出..."
        exit 1
    fi
fi

# 检查API Key
if grep -q "sk-your-api-key-here" .env; then
    echo ""
    echo "============================================"
    echo -e "${RED}[重要] 请先配置您的OpenAI API Key！${NC}"
    echo "============================================"
    echo "请用文本编辑器打开 .env 文件"
    echo "将 OPENAI_API_KEY=sk-your-api-key-here"
    echo "改成您的真实API Key"
    echo "例如: OPENAI_API_KEY=sk-xxxxxxx"
    echo ""
    echo "配置完成后，重新运行此脚本"
    echo "============================================"
    read -p "按回车键退出..."
    exit 1
fi

echo -e "${GREEN}[启动中] 正在启动股票研究系统...${NC}"
echo -e "${YELLOW}[提示] 按 Ctrl+C 可以停止系统${NC}"
echo ""

streamlit run app.py --server.headless true --browser.gatherUsageStats false
