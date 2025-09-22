#!/bin/bash

# 网站监控系统停止脚本

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== 停止网站监控系统 ===${NC}"

# 查找运行中的进程
PIDS=$(pgrep -f "python.*app.py\|gunicorn.*run:app" || true)

if [ -z "$PIDS" ]; then
    echo -e "${YELLOW}未找到运行中的网站监控进程${NC}"
    exit 0
fi

echo "找到以下运行中的进程:"
for PID in $PIDS; do
    echo "PID: $PID - $(ps -p $PID -o command --no-headers 2>/dev/null || echo '进程已结束')"
done

echo
read -p "是否停止这些进程？(Y/n): " -n 1 -r
echo

if [[ $REPLY =~ ^[Nn]$ ]]; then
    echo "取消操作"
    exit 0
fi

# 优雅停止进程
echo "正在停止进程..."
for PID in $PIDS; do
    if kill -0 $PID 2>/dev/null; then
        echo "停止进程 $PID..."
        kill -TERM $PID 2>/dev/null || true

        # 等待进程结束
        for i in {1..10}; do
            if ! kill -0 $PID 2>/dev/null; then
                break
            fi
            sleep 1
        done

        # 如果进程仍在运行，强制终止
        if kill -0 $PID 2>/dev/null; then
            echo "强制终止进程 $PID..."
            kill -KILL $PID 2>/dev/null || true
        fi
    fi
done

echo -e "${GREEN}网站监控系统已停止${NC}"