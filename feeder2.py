#!/usr/bin/env python3
"""
Prosty automatyczny karmnik - tylko Raspberry Pi
Harmonogram konfigurowany przez plik JSON
"""

import time
import json
import signal
import sys
from datetime import datetime
from gpiozero import Servo
from gpiozero.pins.pigpio import PiGPIOFactory
import schedule
import logging

# Konfiguracja logowania
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('feeder.log'),
        logging.StreamHandler()
    ]
)


class SimpleFeeder:
    def __init__(self, servo_pin=18, config_file='config.json'):
        """Inicjalizacja karmnika"""
        self.servo_pin = servo_pin
        self.config_file = config_file
        self.servo = None
        self.schedules = []
        self.running = True

        # Inicjalizacja servo
        self.init_servo()

        # Wczytaj konfigurację
        self.load_config()

        # Załaduj harmonogram
        self.setup_schedule()

        logging.info("=== Karmnik uruchomiony ===")
        self.print_status()

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
            logging.info(f"✓ Servo zainicjalizowane na GPIO {self.servo_pin}")
        except Exception as e:
            logging.error(f"✗ Błąd inicjalizacji servo: {e}")
            sys.exit(1)

    def feed(self):
        """Wykonaj karmienie - obrót servo"""
        if self.servo is None:
            logging.error("Servo nie jest zainicjalizowane")
            return False

        try:
            logging.info("🍖 Rozpoczynam karmienie...")

            # Pozycja początkowa
            self.servo.min()
            time.sleep(0.5)

            # Obrót do pozycji karmienia
            self.servo.max()
            time.sleep(1.0)

            # Powrót do pozycji początkowej
            self.servo.min()
            time.sleep(0.5)

            # Detach servo
            self.servo.detach()

            logging.info("✓ Karmienie zakończone")
            return True

        except Exception as e:
            logging.error(f"✗ Błąd podczas karmienia: {e}")
            return False

    def load_config(self):
        """Wczytaj konfigurację z pliku JSON"""
        try:
            with open(self.config_file, 'r') as f:
                config = json.load(f)
                self.schedules = config.get('schedules', [])
            logging.info(f"✓ Konfiguracja wczytana: {len(self.schedules)} harmonogramów")
        except FileNotFoundError:
            logging.info("⚠ Brak pliku konfiguracji, tworzę domyślny...")
            self.create_default_config()
        except Exception as e:
            logging.error(f"✗ Błąd wczytywania konfiguracji: {e}")
            self.schedules = []

    def create_default_config(self):
        """Stwórz domyślny plik konfiguracji"""
        default_config = {
            "schedules": [
                "08:00",
                "12:00",
                "18:00"
            ],
            "description": "Godziny karmienia w formacie HH:MM (24h)"
        }

        try:
            with open(self.config_file, 'w') as f:
                json.dump(default_config, f, indent=2)
            self.schedules = default_config['schedules']
            logging.info(f"✓ Utworzono domyślny config.json z harmonogramem: {', '.join(self.schedules)}")
        except Exception as e:
            logging.error(f"✗ Błąd tworzenia konfiguracji: {e}")

    def setup_schedule(self):
        """Skonfiguruj harmonogram na podstawie config.json"""
        schedule.clear()

        if not self.schedules:
            logging.warning("⚠ Brak harmonogramu karmienia!")
            return

        for feed_time in self.schedules:
            try:
                schedule.every().day.at(feed_time).do(self.scheduled_feed, feed_time)
                logging.info(f"✓ Harmonogram dodany: {feed_time}")
            except Exception as e:
                logging.error(f"✗ Błąd dodawania harmonogramu {feed_time}: {e}")

    def scheduled_feed(self, feed_time):
        """Zaplanowane karmienie"""
        logging.info(f"⏰ HARMONOGRAM: Karmienie o {feed_time}")
        self.feed()

    def print_status(self):
        """Wyświetl status karmnika"""
        logging.info("=" * 50)
        logging.info("STATUS KARMNIKA")
        logging.info("=" * 50)
        logging.info(f"GPIO Pin: {self.servo_pin}")
        logging.info(f"Plik konfiguracji: {self.config_file}")
        logging.info(f"Liczba harmonogramów: {len(self.schedules)}")
        if self.schedules:
            logging.info("Godziny karmienia:")
            for feed_time in sorted(self.schedules):
                logging.info(f"  - {feed_time}")
        else:
            logging.info("  (brak harmonogramu)")
        logging.info("=" * 50)
        logging.info("")
        logging.info("Komendy:")
        logging.info("  - Aby zmienić harmonogram, edytuj: config.json")
        logging.info("  - Aby przeładować config: sudo systemctl restart feeder")
        logging.info("  - Aby zatrzymać: Ctrl+C")
        logging.info("")

    def run(self):
        """Główna pętla programu"""
        logging.info("🚀 Karmnik działa... Naciśnij Ctrl+C aby zatrzymać")
        logging.info("")

        try:
            while self.running:
                schedule.run_pending()
                time.sleep(1)
        except KeyboardInterrupt:
            logging.info("\n⚠ Otrzymano sygnał zatrzymania...")
        finally:
            self.cleanup()

    def cleanup(self):
        """Cleanup przy zamykaniu"""
        self.running = False
        if self.servo:
            try:
                self.servo.close()
            except:
                pass
        logging.info("✓ Karmnik zatrzymany")


def signal_handler(signum, frame):
    """Obsługa sygnałów systemowych"""
    logging.info("\n⚠ Otrzymano sygnał zatrzymania...")
    sys.exit(0)


def main():
    """Główna funkcja"""
    # Obsługa Ctrl+C i systemctl stop
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Uruchom karmnik
    feeder = SimpleFeeder(servo_pin=18, config_file='config.json')
    feeder.run()


if __name__ == "__main__":
    main()