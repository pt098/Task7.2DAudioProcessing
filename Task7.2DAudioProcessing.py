import os
import json
import pyaudio
from vosk import Model, KaldiRecognizer
import gpiod
from gpiod.line import Direction, Value

# Initialize the LED pin
LED_PIN = 17

# Setup GPIO using gpiod
try:
    chip = gpiod.Chip('/dev/gpiochip4')  # Accessing the GPIO chip
    config = {LED_PIN: gpiod.LineSettings(direction=Direction.OUTPUT, output_value=Value.INACTIVE)}
    led_line = chip.request_lines(consumer='led_controller', config=config)  # Request the line for output
except FileNotFoundError as e:
    print(f"Error: {e}")
    exit(1)
except Exception as e:
    print(f"An unexpected error occurred: {e}")
    exit(1)

# Initialize the Vosk model
model_path = "/home/pi/vosk-model" if not os.path.exists(model_path):
    print("Please download the Vosk model and unpack it in the specified path.")
    exit(1)

model = Model(model_path)
recognizer = KaldiRecognizer(model, 16000)

# Initialize PyAudio
p = pyaudio.PyAudio()

# Open the audio stream
stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=4096, input_device_index=0)
stream.start_stream()

print("Listening for 'ON' or 'OFF' commands...")

try:
    while True:
        # Read the audio data
        data = stream.read(4096, exception_on_overflow=False)  # Prevent PyAudio overflow error

        if len(data) == 0:
            continue

        # Perform speech recognition
        if recognizer.AcceptWaveform(data):
            result = json.loads(recognizer.Result())  # Parse the result as JSON

            # Extract the recognized text
            text = result.get('text', '').lower()

            # Check for "on" and "off" commands
            if "on" in text:
                print("Turning LED ON")
                led_line.set_value(LED_PIN, Value.ACTIVE)  # Turn the LED ON
            elif "off" in text:
                print("Turning LED OFF")
                led_line.set_value(LED_PIN, Value.INACTIVE)  # Turn the LED OFF

except KeyboardInterrupt:
    print("Stopping the program ")

finally:
    # Cleanup resources
    led_line.set_value(LED_PIN, Value.INACTIVE)  # Turn off the LED before exiting
    stream.stop_stream()
    stream.close()
    p.terminate()
