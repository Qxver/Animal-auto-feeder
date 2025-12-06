#!/bin/bash
# Skrypt do zarządzania karmnikiem

FEEDER_DIR="/home/admin/feeder"
CONFIG_FILE="$FEEDER_DIR/config.json"

show_help() {
    echo "Karmnik - System Zarządzania"
    echo ""
    echo "Użycie: ./feeder.sh [komenda]"
    echo ""
    echo "Komendy:"
    echo "  start         Uruchom karmnik"
    echo "  stop          Zatrzymaj karmnik"
    echo "  restart       Zrestartuj karmnik"
    echo "  status        Pokaż status"
    echo "  logs          Pokaż logi na żywo"
    echo "  test          Test servo (jednorazowe karmienie)"
    echo "  schedule      Pokaż harmonogram"
    echo "  edit          Edytuj harmonogram"
    echo "  add [HH:MM]   Dodaj godzinę karmienia"
    echo "  remove [HH:MM] Usuń godzinę karmienia"
    echo ""
}

test_feed() {
    echo "Test karmienia..."
    cd "$FEEDER_DIR"
    python3 << 'EOF'
from feeder_simple import SimpleFeeder
import sys
feeder = SimpleFeeder()
success = feeder.feed()
sys.exit(0 if success else 1)
EOF
    if [ $? -eq 0 ]; then
        echo "Test zakończony pomyślnie"
    else
        echo "Test nie powiódł się"
    fi
}

show_schedule() {
    if [ ! -f "$CONFIG_FILE" ]; then
        echo "Brak pliku konfiguracji"
        return
    fi

    echo "Harmonogram karmienia:"
    echo ""
    python3 << EOF
import json
with open('$CONFIG_FILE', 'r') as f:
    config = json.load(f)
    schedules = config.get('schedules', [])
    if not schedules:
        print("  (brak harmonogramu)")
    else:
        for time in sorted(schedules):
            print(f"  🕐 {time}")
EOF
}

add_schedule() {
    if [ -z "$1" ]; then
        echo "Podaj godzinę w formacie HH:MM"
        echo "Przykład: ./feeder.sh add 14:30"
        return
    fi

    TIME="$1"

    # Walidacja formatu
    if ! [[ "$TIME" =~ ^([01][0-9]|2[0-3]):[0-5][0-9]$ ]]; then
        echo "Nieprawidłowy format. Użyj HH:MM (np. 14:30)"
        return
    fi

    python3 << EOF
import json
with open('$CONFIG_FILE', 'r') as f:
    config = json.load(f)

if '$TIME' in config['schedules']:
    print("Godzina $TIME już istnieje w harmonogramie")
else:
    config['schedules'].append('$TIME')
    config['schedules'].sort()
    with open('$CONFIG_FILE', 'w') as f:
        json.dump(config, f, indent=2)
    print("Dodano godzinę $TIME")
    print("Pamiętaj zrestartować karmnik: sudo systemctl restart feeder")
EOF
}

remove_schedule() {
    if [ -z "$1" ]; then
        echo "Podaj godzinę do usunięcia"
        echo "Przykład: ./feeder.sh remove 14:30"
        return
    fi

    TIME="$1"

    python3 << EOF
import json
with open('$CONFIG_FILE', 'r') as f:
    config = json.load(f)

if '$TIME' in config['schedules']:
    config['schedules'].remove('$TIME')
    with open('$CONFIG_FILE', 'w') as f:
        json.dump(config, f, indent=2)
    print("Usunięto godzinę $TIME")
    print("Pamiętaj zrestartować karmnik: sudo systemctl restart feeder")
else:
    print("Godzina $TIME nie istnieje w harmonogramie")
EOF
}

case "$1" in
    start)
        echo "Uruchamianie karmnika..."
        sudo systemctl start feeder.service
        sleep 2
        sudo systemctl status feeder.service --no-pager
        ;;
    stop)
        echo "Zatrzymywanie karmnika..."
        sudo systemctl stop feeder.service
        ;;
    restart)
        echo "🔄 Restart karmnika..."
        sudo systemctl restart feeder.service
        sleep 2
        sudo systemctl status feeder.service --no-pager
        ;;
    status)
        sudo systemctl status feeder.service
        ;;
    logs)
        echo "Logi karmnika (Ctrl+C aby wyjść)..."
        sudo journalctl -u feeder.service -f
        ;;
    test)
        test_feed
        ;;
    schedule)
        show_schedule
        ;;
    edit)
        nano "$CONFIG_FILE"
        echo ""
        echo "Zrestartuj karmnik aby zastosować zmiany:"
        echo "  sudo systemctl restart feeder.service"
        ;;
    add)
        add_schedule "$2"
        ;;
    remove)
        remove_schedule "$2"
        ;;
    help|--help|-h|"")
        show_help
        ;;
    *)
        echo "Nieznana komenda: $1"
        echo ""
        show_help
        exit 1
        ;;
esac