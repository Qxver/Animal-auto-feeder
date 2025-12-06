#!/bin/bash

echo "=== Instalacja panelu web dla karmnika ==="
echo ""

# Instalacja Flask
echo "1. Instalacja Flask..."
pip3 install flask --break-system-packages

# Kopiowanie pliku
echo "2. Kopiowanie feeder_web_page.py..."
cp feeder_web_page.py /home/admin/feeder/
chmod +x /home/admin/feeder/feeder_web_page.py

# Nadaj uprawnienia sudo bez hasła dla restartu usługi
echo "3. Konfiguracja uprawnień sudo..."
sudo tee /etc/sudoers.d/feeder > /dev/null << 'EOF'
admin ALL=(ALL) NOPASSWD: /usr/bin/systemctl restart feeder.service
admin ALL=(ALL) NOPASSWD: /usr/bin/systemctl start feeder.service
admin ALL=(ALL) NOPASSWD: /usr/bin/systemctl stop feeder.service
EOF

sudo chmod 440 /etc/sudoers.d/feeder

# Tworzenie usługi systemd dla serwera web
echo "4. Tworzenie usługi feeder-web..."
sudo tee /etc/systemd/system/feeder-web.service > /dev/null << 'EOF'
[Unit]
Description=Feeder Web Panel
After=network.target

[Service]
Type=simple
User=admin
WorkingDirectory=/home/admin/feeder
ExecStart=/usr/bin/python3 /home/admin/feeder/feeder_web_page.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# Reload i start
echo "5. Uruchamianie serwera web..."
sudo systemctl daemon-reload
sudo systemctl enable feeder-web.service
sudo systemctl start feeder-web.service

# Sprawdź IP
IP=$(hostname -I | awk '{print $1}')

echo ""
echo "==================================="
echo "✓ Panel web zainstalowany!"
echo "==================================="
echo ""
echo "Otwórz w przeglądarce:"
echo "  http://$IP:5000"
echo ""
echo "Lub na tym samym urządzeniu:"
echo "  http://localhost:5000"
echo ""
echo "Komendy:"
echo "  sudo systemctl status feeder-web    - status"
echo "  sudo systemctl restart feeder-web   - restart"
echo "  sudo journalctl -u feeder-web -f    - logi"
echo ""