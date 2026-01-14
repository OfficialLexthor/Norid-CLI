#!/bin/bash
# Norid CLI - Interaktivt menysystem for Linux
# Kjør med: ./norid.sh

cd "$(dirname "$0")"

# Farger
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
GRAY='\033[0;90m'
NC='\033[0m'
BOLD='\033[1m'

# Miljøvalg (prod eller test)
USE_TEST=""
ENV_NAME="Produksjon"

show_logo() {
    clear
    echo -e "${CYAN}"
    echo '  _   _            _     _    ____ _     ___ '
    echo ' | \ | | ___  _ __(_) __| |  / ___| |   |_ _|'
    echo ' |  \| |/ _ \| '\''__| |/ _` | | |   | |    | | '
    echo ' | |\  | (_) | |  | | (_| | | |___| |___ | | '
    echo ' |_| \_|\___/|_|  |_|\__,_|  \____|_____|___|'
    echo -e "${NC}"
    echo -e "${GRAY}──────────────────────────────────────────────────${NC}"
    echo -e "${GRAY}  Slå opp .no-domener uten autentisering${NC}"
    echo -e "${GRAY}──────────────────────────────────────────────────${NC}"
    echo ""
}

# Opprett venv hvis det ikke finnes
setup_env() {
    if [ ! -d "venv" ]; then
        echo -e "${YELLOW}▸ Oppretter virtuelt miljø...${NC}"
        python3 -m venv venv
        source venv/bin/activate
        echo -e "${YELLOW}▸ Installerer avhengigheter...${NC}"
        pip install -q -r requirements.txt
        echo -e "${GREEN}✓ Ferdig!${NC}"
        sleep 1
    else
        source venv/bin/activate
    fi
}

run_cmd() {
    echo ""
    python norid_cli.py $USE_TEST "$@"
    echo ""
    echo -e "${GRAY}Trykk Enter for å fortsette...${NC}"
    read
}

# === DOMENEOPPSLAG ===
menu_domain() {
    while true; do
        show_logo
        echo -e "${BOLD}🔍 DOMENEOPPSLAG (RDAP)${NC} ${GRAY}[$ENV_NAME]${NC}"
        echo ""
        echo -e "  ${CYAN}1)${NC} Slå opp domene"
        echo -e "  ${CYAN}2)${NC} Sjekk om domene eksisterer"
        echo -e "  ${CYAN}3)${NC} Vis som JSON"
        echo ""
        echo -e "  ${CYAN}0)${NC} ← Tilbake til hovedmeny"
        echo ""
        read -p "Valg: " choice

        case $choice in
            1)
                echo ""
                read -p "Domenenavn (f.eks. norid.no): " domain
                if [ -n "$domain" ]; then
                    run_cmd domain "$domain"
                fi
                ;;
            2)
                echo ""
                read -p "Domenenavn (f.eks. norid.no): " domain
                if [ -n "$domain" ]; then
                    run_cmd domain "$domain" --available
                fi
                ;;
            3)
                echo ""
                read -p "Domenenavn (f.eks. norid.no): " domain
                if [ -n "$domain" ]; then
                    run_cmd domain "$domain" --json
                fi
                ;;
            0|"") break ;;
        esac
    done
}

# === DAS (LEDIG DOMENE) ===
do_das() {
    show_logo
    echo -e "${BOLD}✓ SJEKK OM DOMENE ER LEDIG (DAS)${NC} ${GRAY}[$ENV_NAME]${NC}"
    echo ""
    read -p "Domenenavn (f.eks. example.no): " domain
    if [ -n "$domain" ]; then
        run_cmd das "$domain"
    fi
}

# === WHOIS ===
do_whois() {
    show_logo
    echo -e "${BOLD}📋 WHOIS-OPPSLAG${NC} ${GRAY}[$ENV_NAME]${NC}"
    echo ""
    read -p "Domenenavn (f.eks. norid.no): " domain
    if [ -n "$domain" ]; then
        run_cmd whois "$domain"
    fi
}

# === ENTITETSOPPSLAG ===
menu_entity() {
    while true; do
        show_logo
        echo -e "${BOLD}👤 ENTITETSOPPSLAG${NC} ${GRAY}[$ENV_NAME]${NC}"
        echo ""
        echo -e "  ${CYAN}1)${NC} Slå opp registrar"
        echo -e "  ${CYAN}2)${NC} Slå opp kontaktperson"
        echo -e "  ${CYAN}3)${NC} Vis som JSON"
        echo ""
        echo -e "  ${CYAN}0)${NC} ← Tilbake til hovedmeny"
        echo ""
        read -p "Valg: " choice

        case $choice in
            1)
                echo ""
                echo -e "${GRAY}Eksempel: reg1-NORID, reg1103-NORID${NC}"
                read -p "Registrar-handle: " handle
                if [ -n "$handle" ]; then
                    run_cmd entity "$handle"
                fi
                ;;
            2)
                echo ""
                echo -e "${GRAY}Eksempel: NH55R-NORID${NC}"
                read -p "Kontakt-handle: " handle
                if [ -n "$handle" ]; then
                    run_cmd entity "$handle"
                fi
                ;;
            3)
                echo ""
                read -p "Handle: " handle
                if [ -n "$handle" ]; then
                    run_cmd entity "$handle" --json
                fi
                ;;
            0|"") break ;;
        esac
    done
}

# === NAVNESERVEROPPSLAG ===
menu_nameserver() {
    while true; do
        show_logo
        echo -e "${BOLD}🖥️  NAVNESERVEROPPSLAG${NC} ${GRAY}[$ENV_NAME]${NC}"
        echo ""
        echo -e "  ${CYAN}1)${NC} Slå opp navneserver (via handle)"
        echo -e "  ${CYAN}2)${NC} Søk etter navneservere (via hostname)"
        echo -e "  ${CYAN}3)${NC} Vis som JSON"
        echo ""
        echo -e "  ${CYAN}0)${NC} ← Tilbake til hovedmeny"
        echo ""
        read -p "Valg: " choice

        case $choice in
            1)
                echo ""
                echo -e "${GRAY}Eksempel: X11H-NORID${NC}"
                read -p "Navneserver-handle: " handle
                if [ -n "$handle" ]; then
                    run_cmd nameserver "$handle"
                fi
                ;;
            2)
                echo ""
                echo -e "${GRAY}Eksempel: x.nic.no eller *.nic.no${NC}"
                read -p "Hostname/mønster: " pattern
                if [ -n "$pattern" ]; then
                    run_cmd search nameservers "$pattern"
                fi
                ;;
            3)
                echo ""
                read -p "Navneserver-handle: " handle
                if [ -n "$handle" ]; then
                    run_cmd nameserver "$handle" --json
                fi
                ;;
            0|"") break ;;
        esac
    done
}

# === INNSTILLINGER ===
menu_settings() {
    while true; do
        show_logo
        echo -e "${BOLD}⚙️  INNSTILLINGER${NC}"
        echo ""
        if [ -z "$USE_TEST" ]; then
            echo -e "  Nåværende miljø: ${GREEN}Produksjon${NC}"
        else
            echo -e "  Nåværende miljø: ${YELLOW}Test${NC}"
        fi
        echo ""
        echo -e "  ${CYAN}1)${NC} Bytt til produksjonsmiljø"
        echo -e "  ${CYAN}2)${NC} Bytt til testmiljø"
        echo ""
        echo -e "  ${CYAN}0)${NC} ← Tilbake til hovedmeny"
        echo ""
        read -p "Valg: " choice

        case $choice in
            1)
                USE_TEST=""
                ENV_NAME="Produksjon"
                echo -e "\n${GREEN}✓ Byttet til produksjonsmiljø${NC}"
                sleep 1
                ;;
            2)
                USE_TEST="--test"
                ENV_NAME="Test"
                echo -e "\n${YELLOW}✓ Byttet til testmiljø${NC}"
                sleep 1
                ;;
            0|"") break ;;
        esac
    done
}

# === AVANSERT MODUS ===
advanced_mode() {
    show_logo
    echo -e "${BOLD}📖 AVANSERT MODUS${NC} - Skriv kommandoer direkte"
    echo -e "${GRAY}Skriv 'exit' for å gå tilbake til menyen${NC}"
    echo -e "${GRAY}Skriv 'help' for å se tilgjengelige kommandoer${NC}"
    echo ""
    while true; do
        echo -ne "${GREEN}norid${NC}${BOLD}>${NC} "
        read cmd
        if [ "$cmd" = "exit" ] || [ "$cmd" = "quit" ]; then
            break
        fi
        if [ "$cmd" = "help" ]; then
            python norid_cli.py --help
        elif [ -n "$cmd" ]; then
            python norid_cli.py $USE_TEST $cmd
        fi
        echo ""
    done
}

# === HOVEDMENY ===
main_menu() {
    while true; do
        show_logo
        echo -e "${BOLD}HOVEDMENY${NC} ${GRAY}[$ENV_NAME]${NC}"
        echo ""
        echo -e "  ${CYAN}1)${NC} 🔍 Domeneoppslag (RDAP)"
        echo -e "  ${CYAN}2)${NC} ✓  Sjekk om ledig (DAS)"
        echo -e "  ${CYAN}3)${NC} 📋 Whois-oppslag"
        echo -e "  ${CYAN}4)${NC} 👤 Entitetsoppslag"
        echo -e "  ${CYAN}5)${NC} 🖥️  Navneserveroppslag"
        echo ""
        echo -e "  ${CYAN}8)${NC} ⚙️  Innstillinger"
        echo -e "  ${CYAN}9)${NC} 📖 Avansert modus"
        echo -e "  ${CYAN}0)${NC} 🚪 Avslutt"
        echo ""
        read -p "Valg: " choice

        case $choice in
            1) menu_domain ;;
            2) do_das ;;
            3) do_whois ;;
            4) menu_entity ;;
            5) menu_nameserver ;;
            8) menu_settings ;;
            9) advanced_mode ;;
            0|"")
                show_logo
                echo -e "${CYAN}Ha det! 👋${NC}"
                echo ""
                exit 0
                ;;
        esac
    done
}

# Start
setup_env
main_menu
