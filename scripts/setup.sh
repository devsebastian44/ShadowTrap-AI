#!/bin/bash
# ShadowTrap AI - Setup Script
set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}"
echo "  ███████╗██╗  ██╗ █████╗ ██████╗  ██████╗ ██╗    ██╗"
echo "  ██╔════╝██║  ██║██╔══██╗██╔══██╗██╔═══██╗██║    ██║"
echo "  ███████╗███████║███████║██║  ██║██║   ██║██║ █╗ ██║"
echo "  ╚════██║██╔══██║██╔══██║██║  ██║██║   ██║██║███╗██║"
echo "  ███████║██║  ██║██║  ██║██████╔╝╚██████╔╝╚███╔███╔╝"
echo "  ╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═════╝  ╚═════╝  ╚══╝╚══╝ "
echo "                    T R A P    A I"
echo -e "${NC}"

echo -e "${YELLOW}[1/5] Checking dependencies...${NC}"
command -v docker >/dev/null 2>&1 || { echo -e "${RED}Docker not found. Please install Docker.${NC}"; exit 1; }
command -v docker compose >/dev/null 2>&1 || { echo -e "${RED}Docker Compose not found.${NC}"; exit 1; }

echo -e "${YELLOW}[2/5] Setting up environment...${NC}"
if [ ! -f backend/.env ]; then
    cp backend/.env.example backend/.env
    echo -e "${GREEN}  ✅ Created backend/.env from template${NC}"
    echo -e "${YELLOW}  ⚠️  Edit backend/.env to configure Telegram/Discord alerts${NC}"
else
    echo -e "  backend/.env already exists, skipping."
fi

echo -e "${YELLOW}[3/5] Setting up iptables redirect (port 22 → 2222)...${NC}"
echo -e "${RED}⚠️ WARNING: If you are running this on a remote server, redirecting port 22 will LOCK YOU OUT unless your real SSH daemon is running on a different port (e.g., 2224).${NC}"
read -p "Have you changed your real SSH port and wish to proceed with the redirect? [y/N]: " proceed_iptables
if [[ "$proceed_iptables" =~ ^[Yy]$ ]]; then
    if command -v iptables >/dev/null 2>&1; then
        sudo iptables -t nat -A PREROUTING -p tcp --dport 22 -j REDIRECT --to-port 2222 2>/dev/null && \
            echo -e "${GREEN}  ✅ iptables rule added: port 22 → 2222${NC}" || \
            echo -e "${YELLOW}  ⚠️  Could not add iptables rule (run as root or add manually)${NC}"
    else
        echo -e "${YELLOW}  ⚠️  iptables not found. Add port redirect manually.${NC}"
    fi
else
    echo -e "${YELLOW}  ⏭️ Skipping iptables redirect. You will need to add it manually later.${NC}"
fi

echo -e "${YELLOW}[4/5] Pulling Docker images...${NC}"
docker compose pull

echo -e "${YELLOW}[5/5] Starting ShadowTrap AI...${NC}"
docker compose up -d --build

echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}  ✅ ShadowTrap AI is running!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "  🖥️  Dashboard:    http://localhost:8080"
echo "  🔌  API Docs:     http://localhost:8000/api/docs"
echo "  🗄️  Mongo Admin:  http://localhost:8081  (run with --profile debug)"
echo "  🕷️  Honeypot SSH: port 2222"
echo ""
echo -e "${YELLOW}  Logs: docker compose logs -f${NC}"
echo ""
