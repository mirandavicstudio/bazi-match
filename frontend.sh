#!/usr/bin/env bash
# 八字合盘 - 前端管理脚本 (Git Bash / WSL)
# 用法: ./frontend.sh [start|stop|restart|status]

FRONTEND_DIR="$(cd "$(dirname "$0")/frontend" && pwd)"
PORT=3000
PID_FILE="$(dirname "$0")/.frontend.pid"

start_frontend() {
    echo ""
    echo "[启动] 正在启动前端服务..."
    echo "[启动] 目录: $FRONTEND_DIR"
    echo "[启动] 端口: $PORT"

    # 检查端口是否已被占用
    if lsof -i ":$PORT" -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo "[错误] 端口 $PORT 已被占用！"
        echo "[提示] 请先运行 stop 终止已有服务，或修改脚本中的 PORT 变量"
        return 1
    fi

    # 检查前端目录
    if [ ! -f "$FRONTEND_DIR/index.html" ]; then
        echo "[错误] 未找到 $FRONTEND_DIR/index.html"
        return 1
    fi

    # 使用 Python 启动 HTTP 服务器
    echo "[启动] 使用 Python HTTP 服务器..."
    cd "$FRONTEND_DIR"
    python -m http.server $PORT --bind 127.0.0.1 >/dev/null 2>&1 &
    local PID=$!
    echo $PID > "$PID_FILE"

    # 等待并验证
    sleep 2
    if kill -0 $PID 2>/dev/null; then
        echo "[成功] 前端服务已启动！"
        echo "[成功] PID: $PID"
        echo "[成功] 访问地址: http://localhost:$PORT"
        echo ""
        echo "提示：后端 API 地址应为 http://localhost:8000"
    else
        echo "[警告] 服务可能未成功启动，请检查端口 $PORT 是否可用"
        rm -f "$PID_FILE"
        return 1
    fi
}

stop_frontend() {
    echo ""
    echo "[终止] 正在终止前端服务..."

    if [ -f "$PID_FILE" ]; then
        local SAVED_PID=$(cat "$PID_FILE")
        if kill -0 "$SAVED_PID" 2>/dev/null; then
            kill "$SAVED_PID" 2>/dev/null
            echo "[成功] 已终止进程 PID: $SAVED_PID"
        else
            echo "[提示] PID $SAVED_PID 进程不存在"
        fi
        rm -f "$PID_FILE"
    fi

    # 兜底：按端口查找并终止
    local PORT_PID
    if command -v lsof &>/dev/null; then
        PORT_PID=$(lsof -i ":$PORT" -sTCP:LISTEN -t 2>/dev/null)
    elif command -v ss &>/dev/null; then
        PORT_PID=$(ss -tlnp "sport = :$PORT" 2>/dev/null | grep -oP 'pid=\K[0-9]+' | head -1)
    fi

    if [ -n "$PORT_PID" ]; then
        kill "$PORT_PID" 2>/dev/null
        echo "[成功] 已终止占用端口 $PORT 的进程 PID: $PORT_PID"
    fi

    echo "[完成] 前端服务已终止"
}

status_frontend() {
    echo ""
    echo "[状态] 检查前端服务状态..."
    echo "[状态] 端口: $PORT"

    local IS_RUNNING=false
    if command -v lsof &>/dev/null; then
        if lsof -i ":$PORT" -sTCP:LISTEN -t >/dev/null 2>&1; then
            local PID=$(lsof -i ":$PORT" -sTCP:LISTEN -t 2>/dev/null | head -1)
            echo "[运行中] 前端服务正在运行，PID: $PID"
            echo "[运行中] 访问地址: http://localhost:$PORT"
            IS_RUNNING=true
        fi
    fi

    if [ "$IS_RUNNING" = false ]; then
        echo "[未运行] 前端服务未启动"
    fi

    if [ -f "$PID_FILE" ]; then
        echo "[记录] PID 文件记录: $(cat "$PID_FILE")"
    else
        echo "[记录] 无 PID 文件"
    fi
}

case "${1:-}" in
    start)
        start_frontend
        ;;
    stop)
        stop_frontend
        ;;
    restart)
        stop_frontend
        sleep 1
        start_frontend
        ;;
    status)
        status_frontend
        ;;
    *)
        echo ""
        echo "用法: $0 [start|stop|restart|status]"
        echo ""
        echo "  start    - 启动前端服务"
        echo "  stop     - 终止前端服务"
        echo "  restart  - 重启前端服务"
        echo "  status   - 查看服务状态"
        echo ""
        echo "  不带参数运行将显示此帮助信息"
        ;;
esac
