#!/bin/bash

# Everything About Agent - Start Menu (Linux/macOS)

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="$SCRIPT_DIR/logs"
PID_DIR="$SCRIPT_DIR/.pids"
WEB_DIR="$SCRIPT_DIR/docs/web"

mkdir -p "$LOG_DIR" "$PID_DIR"

find_port() {
    python3 -c "import socket; s=socket.socket(); s.bind(('',0)); print(s.getsockname()[1]); s.close()"
}

show_menu() {
    clear
    echo "================================================"
    echo "   Everything About Agent - Start Menu"
    echo "================================================"
    echo ""
    echo "   1. Install/Update Dependencies"
    echo "   2. Run System Verification"
    echo "   3. Run Prompt Chaining Demo"
    echo "   4. Run Routing Demo"
    echo "   5. Start Web Frontend"
    echo "   6. Start Web with File Watcher"
    echo "   7. Start MkDocs Documentation Server"
    echo "   8. Stop All Services"
    echo "   9. Check Service Status"
    echo "  10. Run Diagnostics"
    echo "  11. View Logs"
    echo "  12. Exit"
    echo ""
    echo "================================================"
    read -p "Please select [1-12]: " choice
}

while true; do
    show_menu
    
    case $choice in
        1)
            echo ""
            echo -e "${BLUE}Installing dependencies...${NC}"
            pip install -e .
            read -p "Press Enter to continue..."
            ;;
        2)
            echo ""
            echo -e "${BLUE}Running system verification...${NC}"
            python tests/test_system.py
            read -p "Press Enter to continue..."
            ;;
        3)
            echo ""
            echo -e "${BLUE}Running Prompt Chaining demo...${NC}"
            python src/agents/patterns/chaining.py
            read -p "Press Enter to continue..."
            ;;
        4)
            echo ""
            echo -e "${BLUE}Running Routing demo...${NC}"
            python src/agents/patterns/routing.py
            read -p "Press Enter to continue..."
            ;;
        5)
            echo ""
            PORT=$(find_port)
            echo "================================================"
            echo "    Everything About Agent - Web Server"
            echo "================================================"
            echo ""
            echo "   ACCESS URL:  http://localhost:$PORT"
            echo ""
            echo "================================================"
            echo ""
            
            cd "$WEB_DIR"
            python3 -m http.server $PORT &
            echo $! > "$PID_DIR/web_server.pid"
            
            sleep 1
            
            # Open browser
            if command -v xdg-open &> /dev/null; then
                xdg-open "http://localhost:$PORT" &
            elif command -v open &> /dev/null; then
                open "http://localhost:$PORT" &
            fi
            
            echo -e "${GREEN}Server started on port $PORT${NC}"
            read -p "Press Enter to continue..."
            ;;
        6)
            echo ""
            PORT=$(find_port)
            echo "================================================"
            echo "    Everything About Agent - Web Server"
            echo "================================================"
            echo ""
            echo "   ACCESS URL:  http://localhost:$PORT"
            echo ""
            echo "   Features: Auto-reload on file changes"
            echo "================================================"
            echo ""
            
            # Check watchdog
            if ! python3 -c "import watchdog" 2>/dev/null; then
                echo -e "${YELLOW}Installing watchdog...${NC}"
                pip install watchdog
            fi
            
            cd "$SCRIPT_DIR"
            python3 scripts/file_watcher.py --port $PORT --dir "$WEB_DIR"
            read -p "Press Enter to continue..."
            ;;
        7)
            echo ""
            PORT=$(find_port)
            echo "================================================"
            echo "    Everything About Agent - MkDocs Docs"
            echo "================================================"
            echo ""
            echo "   ACCESS URL:  http://localhost:$PORT"
            echo ""
            echo "   Features: Material theme, 20 design patterns"
            echo "================================================"
            echo ""

            # Check mkdocs
            if ! python3 -c "import mkdocs" 2>/dev/null; then
                echo -e "${YELLOW}Installing mkdocs...${NC}"
                pip install mkdocs mkdocs-material
            fi

            cd "$SCRIPT_DIR"
            mkdocs serve --dev-addr 0.0.0.0:$PORT &
            echo $! > "$PID_DIR/mkdocs_server.pid"

            sleep 1

            # Open browser
            if command -v xdg-open &> /dev/null; then
                xdg-open "http://localhost:$PORT" &
            elif command -v open &> /dev/null; then
                open "http://localhost:$PORT" &
            fi

            echo -e "${GREEN}MkDocs server started on port $PORT${NC}"
            read -p "Press Enter to continue..."
            ;;
        8)
            echo ""
            echo -e "${YELLOW}Stopping all services...${NC}"
            if [ -f "$PID_DIR/web_server.pid" ]; then
                kill $(cat "$PID_DIR/web_server.pid") 2>/dev/null
                rm -f "$PID_DIR/web_server.pid"
            fi
            # Kill python http.server processes
            pkill -f "python.*http.server" 2>/dev/null
            pkill -f "mkdocs serve" 2>/dev/null
            echo -e "${GREEN}Done${NC}"
            read -p "Press Enter to continue..."
            ;;
        9)
            echo ""
            echo "================================================"
            echo "   Service Status"
            echo "================================================"
            echo ""
            if [ -f "$PID_DIR/web_server.pid" ]; then
                echo "Web Server PID: $(cat $PID_DIR/web_server.pid)"
            else
                echo "Web Server: Not running"
            fi
            if [ -f "$PID_DIR/mkdocs_server.pid" ]; then
                echo "MkDocs Server PID: $(cat $PID_DIR/mkdocs_server.pid)"
            else
                echo "MkDocs Server: Not running"
            fi
            echo ""
            ps aux | grep python | grep -v grep | head -5
            read -p "Press Enter to continue..."
            ;;
        10)
            echo ""
            echo -e "${BLUE}Running diagnostics...${NC}"
            python3 scripts/diagnose.py
            read -p "Press Enter to continue..."
            ;;
        11)
            echo ""
            echo "================================================"
            echo "   Available Logs"
            echo "================================================"
            echo ""
            ls -lt "$LOG_DIR"/*.log 2>/dev/null | head -5
            read -p "Press Enter to continue..."
            ;;
        12)
            echo ""
            echo -e "${GREEN}Goodbye!${NC}"
            exit 0
            ;;
        *)
            echo -e "${RED}Invalid choice${NC}"
            read -p "Press Enter to continue..."
            ;;
    esac
done
