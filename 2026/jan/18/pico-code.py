"""Example for Pico. Turns on the built-in LED."""
import time
import board
import digitalio

led = digitalio.DigitalInOut(board.GP14)
led.direction = digitalio.Direction.OUTPUT

while True:
    led.value = True
    time.sleep(5)
    led.value = False
    time.sleep(5)
