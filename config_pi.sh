#!/bin/bash

echo "=== Instalacja Automatycznego Karmnika ==="

# Aktualizacja systemu
echo "Aktualizacja systemu..."
sudo apt-get update
sudo apt-get upgrade -y

# Instalacja wymaganych pakietów
echo "Instalacja pakietów..."
sudo apt-get install -y python3-pip python3-gpiozero bluetooth bluez python3-bluez pigpio python3-dev libbluetooth-dev

# Uruchomienie pigpio daemon
echo "Uruchamianie pigpio daemon..."
sudo systemctl enable pigpiod
sudo systemctl start pigpiod

# Instalacja bibliotek Python
echo "Instalacja bibliotek Python..."
pip3 install pybluez schedule --break-system-packages 2>/dev/null || pip3 install pybluez schedule

# Konfiguracja Bluetooth
echo "Konfiguracja Bluetooth..."

# Tworzenie katalogu dla projektu
echo "Tworzenie struktury katalogów..."
mkdir -p ~/feeder
cd ~/feeder

# Konfiguracja /etc/bluetooth/main.conf
echo "Konfiguracja main.conf..."
sudo bash -c 'cat > /etc/bluetooth/main.conf << EOF
[General]
Name = FeederPi
Class = 0x000100
DiscoverableTimeout = 0
PairableTimeout = 0
Discoverable = true
Pairable = true

[Policy]
AutoEnable=true
EOF'

# Restart Bluetooth
echo "Restart Bluetooth..."
sudo systemctl restart bluetooth
sleep 3

# Konfiguracja przez bluetoothctl
echo "Ustawianie wykrywalności..."
timeout 10 bluetoothctl << EOF
power on
discoverable on
pairable on
agent NoInputNoOutput
default-agent
EOF

# Nadanie uprawnień wykonywania
chmod +x feeder_main.py 2>/dev/null || true

# Tworzenie usługi systemd
echo "Tworzenie usługi systemd..."
sudo tee /etc/systemd/system/feeder.service > /dev/null <<EOF
[Unit]
Description=Automatic Pet Feeder Service
After=network.target bluetooth.target pigpiod.service
Wants=bluetooth.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$HOME/feeder
ExecStartPre=/bin/sleep 10
ExecStart=/usr/bin/python3 $HOME/feeder/feeder_main.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd
sudo systemctl daemon-reload

# Włączenie usługi
echo "Włączanie usługi..."
sudo systemctl enable feeder.service

# Tworzenie skryptu uruchamiającego Bluetooth przy starcie
echo "Tworzenie skryptu Bluetooth autostart..."
sudo tee /usr/local/bin/bluetooth-discoverable.sh > /dev/null <<'EOF'
#!/bin/bash
sleep 10
bluetoothctl << BTEOF
power on
discoverable on
pairable on
BTEOF
EOF

sudo chmod +x /usr/local/bin/bluetooth-discoverable.sh

# Tworzenie usługi dla autostartu Bluetooth
sudo tee /etc/systemd/system/bluetooth-discoverable.service > /dev/null <<EOF
[Unit]
Description=Make Bluetooth Discoverable
After=bluetooth.target
Requires=bluetooth.target

[Service]
Type=oneshot
ExecStart=/usr/local/bin/bluetooth-discoverable.sh
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable bluetooth-discoverable.service

echo ""
echo "=== Instalacja zakończona ==="
echo ""
echo "Status Bluetooth:"
hciconfig hci0 2>/dev/null || echo "Użyj: bluetoothctl show"
echo ""
echo "Aby uruchomić usługę ręcznie:"
echo "  sudo systemctl start feeder.service"
echo ""
echo "Aby sprawdzić status:"
echo "  sudo systemctl status feeder.service"
echo ""
echo "Aby zobaczyć logi:"
echo "  sudo journalctl -u feeder.service -f"
echo ""
echo "Lub sprawdź plik feeder.log w katalogu ~/feeder"
echo ""
echo "Sprawdź Bluetooth:"
echo "  bluetoothctl show"
echo ""
echo "Uruchom ponownie Raspberry Pi, aby zastosować wszystkie zmiany:"
echo "  sudo reboot"rm