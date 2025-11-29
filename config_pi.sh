#!/bin/bash

echo "Instalacja Automatycznego Karmnika"

echo "Aktualizacja systemu..."
sudo apt-get update
sudo apt-get upgrade -y

echo "Instalacja pakietów..."
sudo apt-get install -y python3-pip python3-gpiozero bluetooth bluez python3-bluez pigpio

echo "Uruchamianie pigpio daemon..."
sudo systemctl enable pigpiod
sudo systemctl start pigpiod

echo "Instalacja bibliotek Python..."
pip3 install pybluez schedule

echo "Konfiguracja Bluetooth..."

sudo sed -i 's/#Class = 0x000100/Class = 0x000100/' /etc/bluetooth/main.conf
sudo sed -i 's/#DiscoverableTimeout = 0/DiscoverableTimeout = 0/' /etc/bluetooth/main.conf

sudo systemctl restart bluetooth

sudo hciconfig hci0 piscan

echo "Tworzenie struktury katalogów..."
mkdir -p ~/feeder
cd ~/feeder

echo "Kopiowanie plików..."

chmod +x feeder_main.py

echo "Tworzenie usługi systemd..."
sudo tee /etc/systemd/system/feeder.service > /dev/null <<EOF
[Unit]
Description=Automatic Pet Feeder Service
After=network.target bluetooth.target pigpiod.service

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/feeder
ExecStart=/usr/bin/python3 /home/pi/feeder/feeder_main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload

echo "Włączanie usługi..."
sudo systemctl enable feeder.service

echo ""
echo "=== Instalacja zakończona ==="
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
echo "Uruchom ponownie Raspberry Pi, aby zastosować wszystkie zmiany:"
echo "  sudo reboot"