import asyncio
import Adafruit_DHT
import json
import time
from nats.aio.client import Client as NATS
from nats.aio.errors import ErrConnectionClosed, ErrTimeout, ErrNoServers

DHT_SENSOR = Adafruit_DHT.DHT22
DHT_PIN = 4

async def run(loop):
    nc = NATS()

    try:
        await nc.connect(servers=["nats://10.8.0.3:4222"], loop=loop)
    except ErrNoServers as e:
        print(e)
        return

    while True:
        humidity, temperature = Adafruit_DHT.read_retry(DHT_SENSOR, DHT_PIN)

        if humidity is not None and temperature is not None:
            print("Temp={0:0.1f}*C  Humidity={1:0.1f}%".format(temperature, humidity))
            humValue = "{:.1f}%".format(humidity)
            tempValue = "{:.1f}*C".format(temperature)

            try:
                await nc.publish("garden", json.dumps({"type": "sensor", "location": "indoor", "temperature": tempValue, "humidity": humValue}).encode())
                await nc.flush(0.500)
            except ErrConnectionClosed as e:
                print("Connection closed prematurely!")
            except ErrTimeout as e:
                print("Timeout occured when publishing msg!")

        time.sleep(60)
    else:
        print("Failed to retrieve data from humidity sensor")

    await nc.close()

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run(loop))
    loop.close()
