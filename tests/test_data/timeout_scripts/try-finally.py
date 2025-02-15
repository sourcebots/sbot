from sbot.internal.timeout import kill_after_delay
import time

kill_after_delay(2)

while True:
    try:
        time.sleep(10)
    finally:
        # Imagine we wanted to do something else here
        pass
