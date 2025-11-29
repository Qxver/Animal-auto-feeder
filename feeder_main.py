#!/usr/bin/env python3
"""
Automatyczny karmnik - główny skrypt dla Raspberry Pi
Obsługuje komunikację Bluetooth i sterowanie servo
"""

import bluetooth
import socket
import json
import threading
import time
from datetime import datetime
from gpiozero import Servo
from gpiozero.pins.pigpio import PiGPIOFactory
import schedule
import logging
import sys

# Konfiguracja logowania
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('feeder.log'),
        logging.StreamHandler()
    ]
)


class AutoFeeder:
    def __init__(self, servo_pin=18):
        """Inicjalizacja karmnika"""
        self.servo_pin = servo_pin
        self.servo = None
        self.schedules = []
        self.schedule_lock = threading.Lock()
        self.running = True

        # Inicjalizacja servo
        self.init_servo()

        logging.info("Karmnik dziala")

    def init_servo(self):
        """Inicjalizacja servo"""
        try:
            factory = PiGPIOFactory()
            self.servo = Servo(
                self.servo_pin,
                pin_factory=factory,
                min_pulse_width=0.5 / 1000,
                max_pulse_width=2.5 / 1000
            )
            logging.info(f"Inicjalizacja serwo {self.servo_pin}")
        except Exception as e:
            logging.error(f"Błąd inicjalizacji servo: {e}")

    def feed(self):
        """Wykonaj karmienie - obrót servo"""
        if self.servo is None:
            logging.error("Servo nie jest zainicjalizowane")
            return False

        try:
            logging.info("Rozpoczynam karmienie...")

            # Pozycja początkowa
            self.servo.min()
            time.sleep(0.5)

            # Obrót do pozycji karmienia
            self.servo.max()
            time.sleep(1.0)

            # Powrót do pozycji początkowej
            self.servo.min()
            time.sleep(0.5)

            # Detach servo aby nie trzymało pozycji
            self.servo.detach()

            logging.info("Karmienie zakończone")
            return True

        except Exception as e:
            logging.error(f"Błąd podczas karmienia: {e}")
            return False

    def update_schedules(self, new_schedules):
        """Aktualizuj harmonogram karmienia"""
        with self.schedule_lock:
            # Wyczyść stary harmonogram
            schedule.clear()
            self.schedules = new_schedules

            # Dodaj nowe zadania
            for time_str in self.schedules:
                schedule.every().day.at(time_str).do(self.scheduled_feed)
                logging.info(f"Dodano harmonogram: {time_str}")

            self.save_schedules()

    def scheduled_feed(self):
        """Zaplanowane karmienie"""
        logging.info("Wykonuję zaplanowane karmienie")
        self.feed()

    def save_schedules(self):
        """Zapisz harmonogram do pliku"""
        try:
            with open('schedules.json', 'w') as f:
                json.dump({'schedules': self.schedules}, f)
            logging.info("Harmonogram zapisany")
        except Exception as e:
            logging.error(f"Błąd zapisu harmonogramu: {e}")

    def load_schedules(self):
        """Wczytaj harmonogram z pliku"""
        try:
            with open('schedules.json', 'r') as f:
                data = json.load(f)
                self.update_schedules(data.get('schedules', []))
            logging.info("Harmonogram wczytany")
        except FileNotFoundError:
            logging.info("Brak zapisanego harmonogramu")
        except Exception as e:
            logging.error(f"Błąd wczytywania harmonogramu: {e}")

    def run_scheduler(self):
        """Uruchom scheduler w osobnym wątku"""
        while self.running:
            schedule.run_pending()
            time.sleep(1)

    def cleanup(self):
        """Cleanup przy zamykaniu"""
        self.running = False
        if self.servo:
            self.servo.close()
        logging.info("Cleanup zakończony")


class BluetoothServer:
    def __init__(self, feeder):
        """Inicjalizacja serwera Bluetooth"""
        self.feeder = feeder
        self.server_sock = None
        self.client_sock = None
        self.running = True

        # UUID dla SPP (Serial Port Profile)
        self.uuid = "00001101-0000-1000-8000-00805F9B34FB"

    def start_server(self):
        """Uruchom serwer Bluetooth"""
        try:
            logging.info("Tworzenie socketu Bluetooth RFCOMM...")
            self.server_sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)

            # Ustawienie opcji socketu
            self.server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

            logging.info("Bindowanie socketu...")
            # Użyj PORT_ANY aby system przydzielił wolny port
            self.server_sock.bind(("", bluetooth.PORT_ANY))

            logging.info("Ustawianie nasłuchiwania...")
            self.server_sock.listen(1)

            port = self.server_sock.getsockname()[1]

            logging.info("Reklamowanie usługi...")
            bluetooth.advertise_service(
                self.server_sock,
                "RaspberryPiFeeder",
                service_id=self.uuid,
                service_classes=[self.uuid, bluetooth.SERIAL_PORT_CLASS],
                profiles=[bluetooth.SERIAL_PORT_PROFILE]
            )

            logging.info(f"Serwer Bluetooth nasłuchuje na porcie RFCOMM {port}")
            logging.info("Czekam na połączenie...")

            while self.running:
                try:
                    self.server_sock.settimeout(1.0)  # Timeout aby móc sprawdzać self.running
                    try:
                        self.client_sock, client_info = self.server_sock.accept()
                        logging.info(f"Połączono z {client_info}")

                        self.send_message("CONNECTED")
                        self.handle_client()
                    except bluetooth.BluetoothError as e:
                        if "timed out" not in str(e):
                            raise
                        continue

                except bluetooth.BluetoothError as e:
                    if self.running:
                        logging.error(f"Błąd Bluetooth: {e}")
                except Exception as e:
                    if self.running:
                        logging.error(f"Błąd: {e}")
                finally:
                    if self.client_sock:
                        try:
                            self.client_sock.close()
                        except:
                            pass
                        self.client_sock = None
                        logging.info("Klient rozłączony")

        except PermissionError as e:
            logging.error(f"Brak uprawnień: {e}")
            logging.error("Uruchom skrypt jako root: sudo python3 feeder_main.py")
            sys.exit(1)
        except Exception as e:
            logging.error(f"Błąd uruchamiania serwera: {e}")
            import traceback
            logging.error(traceback.format_exc())
        finally:
            self.cleanup()

    def handle_client(self):
        """Obsługa połączonego klienta"""
        buffer = ""

        try:
            while self.running:
                data = self.client_sock.recv(1024)
                if not data:
                    break

                buffer += data.decode('utf-8')

                # Przetwarzaj kompletne linie
                while '\n' in buffer:
                    line, buffer = buffer.split('\n', 1)
                    self.process_command(line.strip())

        except bluetooth.BluetoothError:
            logging.info("Klient rozłączony")
        except Exception as e:
            logging.error(f"Błąd obsługi klienta: {e}")

    def process_command(self, command):
        """Przetwórz komendę od klienta"""
        logging.info(f"Otrzymano komendę: {command}")

        try:
            if command == "TEST":
                # Test servo
                success = self.feeder.feed()
                self.send_message("TEST_OK" if success else "TEST_FAILED")

            elif command.startswith("{"):
                # JSON z harmonogramem
                data = json.loads(command)
                schedules = data.get('schedules', [])
                self.feeder.update_schedules(schedules)
                self.send_message(f"SCHEDULES_UPDATED:{len(schedules)}")

            elif command == "GET_SCHEDULES":
                # Wyślij aktualny harmonogram
                response = json.dumps({'schedules': self.feeder.schedules})
                self.send_message(response)

            elif command == "FEED_NOW":
                # Natychmiastowe karmienie
                success = self.feeder.feed()
                self.send_message("FEED_OK" if success else "FEED_FAILED")

            else:
                logging.warning(f"Nieznana komenda: {command}")
                self.send_message("UNKNOWN_COMMAND")

        except json.JSONDecodeError:
            logging.error("Błąd parsowania JSON")
            self.send_message("JSON_ERROR")
        except Exception as e:
            logging.error(f"Błąd przetwarzania komendy: {e}")
            self.send_message(f"ERROR:{str(e)}")

    def send_message(self, message):
        """Wyślij wiadomość do klienta"""
        if self.client_sock:
            try:
                self.client_sock.send((message + "\n").encode('utf-8'))
                logging.info(f"Wysłano: {message}")
            except Exception as e:
                logging.error(f"Błąd wysyłania: {e}")

    def cleanup(self):
        """Cleanup przy zamykaniu"""
        self.running = False
        if self.client_sock:
            try:
                self.client_sock.close()
            except:
                pass
        if self.server_sock:
            try:
                self.server_sock.close()
            except:
                pass
        logging.info("Serwer Bluetooth zamknięty")


def main():
    """Główna funkcja programu"""
    logging.info("Automatyczny Karmnik - Start")

    # Inicjalizacja karmnika
    feeder = AutoFeeder(servo_pin=18)

    # Wczytaj zapisany harmonogram
    feeder.load_schedules()

    # Uruchom scheduler w osobnym wątku
    scheduler_thread = threading.Thread(target=feeder.run_scheduler, daemon=True)
    scheduler_thread.start()
    logging.info("Scheduler uruchomiony")

    # Uruchom serwer Bluetooth
    bt_server = BluetoothServer(feeder)

    try:
        bt_server.start_server()
    except KeyboardInterrupt:
        logging.info("Zatrzymywanie programu...")
    finally:
        feeder.cleanup()
        bt_server.cleanup()
        logging.info("Program zakończony")


if __name__ == "__main__":
    main()