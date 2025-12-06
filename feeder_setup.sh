#!/bin/bash

echo "=== Instalacja prostego karmnika ==="
echo ""

# Zatrzymaj starą usługę jeśli istnieje
sudo systemctl stop feeder.service 2>/dev/null

# Katalog projektu
FEEDER_DIR="/home/admin/feeder"

# Stwórz katalog
mkdir -p "$FEEDER_DIR"
cd "$FEEDER_DIR"

echo "1. Kopiowanie pliku feeder_simple.py..."
cp /home/admin/karmnik/Animal-auto-feeder/feeder.py "$FEEDER_DIR/"
chmod +x feeder.py

echo "2. Tworzenie domyślnego config.json..."
cat > config.json << 'EOF'
{
  "schedules": [
    "08:00",
    "12:00",
    "18:00"
  ],
  "description": "Godziny karmienia w formacie HH:MM (24h)"
}
EOF

echo "3. Tworzenie usługi systemd..."
sudo tee /etc/systemd/system/feeder.service > /dev/null << 'EOF'
[Unit]
Description=Automatic Pet Feeder
After=pigpiod.service
Requires=pigpiod.service

[Service]
Type=simple
User=root
WorkingDirectory=/home/admin/feeder
ExecStart=/usr/bin/python3 /home/admin/feeder/feeder_simple.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

echo "4. Reload systemd..."
sudo systemctl daemon-reload

echo "5. Włączanie usługi..."
sudo systemctl enable feeder.service

echo ""
echo "==================================="
echo "✓ Instalacja zakończona!"
echo "==================================="
echo ""
echo "Aby uruchomić karmnik:"
echo "  sudo systemctl start feeder.service"
echo ""
echo "Aby sprawdzić status:"
echo "  sudo systemctl status feeder.service"
echo ""
echo "Aby zobaczyć logi:"
echo "  sudo journalctl -u feeder.service -f"
echo ""
echo "Aby edytować harmonogram:"
echo "  nano /home/admin/feeder/config.json"
echo "  sudo systemctl restart feeder.service"
echo ""
echo "Aby przetestować servo ręcznie:"
echo "  cd /home/admin/feeder"
echo "  python3 -c 'from feeder_simple import SimpleFeeder; f = SimpleFeeder(); f.feed()'"
echo ""