from gpiozero import Servo
from time import sleep
from gpiozero.pins.pigpio import PiGPIOFactory

factory = PiGPIOFactory()

servo = Servo(18, pin_factory=factory, min_pulse_width=0.5/1000, max_pulse_width=2.5/1000)

print("Test servo MG90S")

try:
    while True:
        servo.min()
        print("0")
        sleep(2)
        servo.mid()
        print("90")
        sleep(2)
        servo.max()
        print("180")
        sleep(2)
except KeyboardInterrupt:
    servo.detach()
    print("\nEnd test.")
