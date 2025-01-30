import asyncio
import Adafruit_DHT
import json
import time
import logging
from logging.handlers import TimedRotatingFileHandler
from nats.aio.client import Client as NATS
from nats.aio.errors import ErrConnectionClosed, ErrTimeout, ErrNoServers

# Setup logging with rotation
log_handler = TimedRotatingFileHandler(
    'sensor_readings.log', 
    when='midnight', 
    interval=1, 
    backupCount=1  # Keep the current and previous day's log
)
log_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
log_handler.suffix = "%Y-%m-%d"  # Add date suffix to log filenames

logging.basicConfig(
    level=logging.INFO,
    handlers=[log_handler]
)

# Function to log and print messages
def log_print(message):
    print(message)
    logging.info(message)

DHT_SENSOR = Adafruit_DHT.DHT22
DHT_PIN = 4

# Cached values to filter out noisy readings
last_temperature = None
last_humidity = None

def is_valid_reading(new_temp, new_humid):
    """
    Checks if the new temperature and humidity readings are valid
    compared to the last cached values.
    """
    global last_temperature, last_humidity

    if last_temperature is not None and last_humidity is not None:
        temp_diff = abs(new_temp - last_temperature)
        humid_diff = abs(new_humid - last_humidity)

        # If the difference exceeds the threshold of 10, discard the reading
        if temp_diff > 10 or humid_diff > 10:
            log_print(
                f"Discarding invalid reading! Temp difference: {temp_diff}, Humidity difference: {humid_diff}"
            )
            return False

    # Update cached values if reading is valid
    last_temperature = new_temp
    last_humidity = new_humid
    return True

async def run(loop):
    nc = NATS()

    try:
        await nc.connect(servers=["nats://10.8.0.3:4222"], loop=loop)
    except ErrNoServers as e:
        log_print(e)
        return

    while True:
        humidity, temperature = Adafruit_DHT.read_retry(DHT_SENSOR, DHT_PIN)

        if humidity is not None and temperature is not None:
            # Check if the new reading is valid
            if is_valid_reading(temperature, humidity):
                log_print("Temp={0:0.1f}*C  Humidity={1:0.1f}%".format(temperature, humidity))

                # Skip error-readings if humidity exceeds 100%
                if humidity > 100:
                    log_print("Detected invalid reading, skipping!")
                    time.sleep(20)
                    continue

                humValue = "{:.1f}".format(humidity)
                tempValue = "{:.1f}".format(temperature)

                try:
                    await nc.publish(
                        "garden",
                        json.dumps({"type": "sensor", "location": "indoor", "temperature": tempValue, "humidity": humValue}).encode()
                    )
                    await nc.flush(0.500)
                except ErrConnectionClosed as e:
                    log_print("Connection closed prematurely!")
                except ErrTimeout as e:
                    log_print("Timeout occurred when publishing msg!")
            else:
                log_print("Using cached values due to invalid reading.")
        else:
            log_print("Failed to retrieve data from humidity sensor")

        time.sleep(20)

    await nc.close()

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run(loop))
    loop.close()
