"""
HC-SR04 with better timing using time.monotonic_ns()
More accurate for short distances
"""

import board
import digitalio
import time

# Setup pins
trig = digitalio.DigitalInOut(board.GP15)
echo = digitalio.DigitalInOut(board.GP14)

trig.direction = digitalio.Direction.OUTPUT
echo.direction = digitalio.Direction.INPUT

trig.value = False

def measure_distance_ns():
    """
    Uses nanosecond timing for better accuracy
    Returns distance in cm or None
    """
    # Send 10µs trigger pulse
    trig.value = True
    # Use time.sleep for 10µs - this is approximate in CircuitPython
    time.sleep(0.00001)
    trig.value = False
    
    # Wait for echo start with timeout
    timeout = time.monotonic_ns() + 100_000_000  # 100ms in nanoseconds
    while not echo.value:
        if time.monotonic_ns() > timeout:
            return None
    
    # Record start time
    start_time = time.monotonic_ns()
    
    # Wait for echo end with timeout
    while echo.value:
        if time.monotonic_ns() > timeout:
            return None
    
    # Record end time
    end_time = time.monotonic_ns()
    
    # Calculate pulse duration in nanoseconds
    pulse_duration_ns = end_time - start_time
    
    # Convert to seconds
    pulse_duration_s = pulse_duration_ns / 1_000_000_000
    
    # Calculate distance
    distance_cm = (pulse_duration_s * 34300) / 2
    
    # Validate range
    if 2 <= distance_cm <= 400:
        return distance_cm
    
    return None

print("HC-SR04 with Nanosecond Timing")
print("==============================")

# Moving average filter
readings = []

while True:
    dist = measure_distance_ns()
    
    if dist is not None:
        # Add to readings (keep last 5)
        readings.append(dist)
        if len(readings) > 5:
            readings.pop(0)
        
        # Calculate average
        avg_dist = sum(readings) / len(readings)
        
        print(f"Distance: {avg_dist:.1f} cm (raw: {dist:.1f} cm)")
        
        # Visual indicator
        bars = min(int(avg_dist / 5), 50)
        print(f"[{'█' * bars}{' ' * (50-bars)}]")
    else:
        print("No valid reading")
    
    time.sleep(0.1)
