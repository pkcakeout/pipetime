"""
A python 3.6 example
"""

import random
import time
import pipetime

from concurrent.futures import ThreadPoolExecutor

reporter = pipetime.ClockReporter(".", plot_interval=10)

def simulate_pipeline(i):
    tracker = reporter.track()
    
    print(f"Loading file {i}")
    time.sleep(3 + random.random() * 2 - 1)
    tracker.time("load file")

    print(f"Augmenting {i}")
    time.sleep(1 + .1 * (random.random() * 2 - 1))
    tracker.time("augmentation")

    print(f"Predicting {i}")
    time.sleep(12 + 11 * (random.random() * 2 - 1))
    tracker.time("prediction")

if __name__ == "__main__":
    with ThreadPoolExecutor(16) as executor:
        for i in range(10000):
            executor.submit(simulate_pipeline, i + 1)
