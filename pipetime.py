import pathlib
import multiprocessing
import queue
import time

import bokeh


class TimeTrail:
    def __init__(self, queue):
        self.__queue = queue
        self.__last = time.time()

    def time(self, name):
        now = time.time()
        delta_t = now - self.__last
        self.__last = now
        self.__queue.put({"cmd": "report", "name": str(name), "delta_t": delta_t})


class ClockReporter:
    @staticmethod
    def create_plot(path, timing_values, timing_counts):
        pass

    @staticmethod
    def __process_handler(rqueue: multiprocessing.Queue, path):
        timing_values = {}
        timing_counts = {}

        mix_factor = 0
        plot_interval = 0

        plot_timeout_start = time.time()
        while True:
            try:
                data = rqueue.get(
                    block=True,
                    timeout=max(0.1, plot_interval * 0.5))
            except queue.Empty:
                cmd = None
                data = None
            else:
                cmd = data["cmd"]

            print(data)

            if cmd is None:
                # Cycle
                if time.time() - plot_timeout_start > plot_interval:
                    plot_timeout_start = time.time()
                    ClockReporter.create_plot(path, timing_values, timing_counts)
                    timing_counts = {k: 0 for k in timing_counts.keys()}
            elif cmd == "exit":
                break
            elif cmd == "set":
                if data["name"] == "mix_factor":
                    mix_factor = float(data["value"])
                if data["name"] == "plot_interval":
                    plot_interval = float(data["value"])
            elif cmd == "report":
                delta_t = float(data["delta_t"])
                new_dt = timing_values.get(data["name"], delta_t)
                new_dt = new_dt * mix_factor + (1 - mix_factor) * delta_t
                timing_values[data["name"]] = new_dt

                timing_counts[data["name"]] = \
                    timing_counts.get(data["name"], 0) + 1
            else:
                raise ValueError("Invalid command: {}".format(data))

    def __init__(self, output_path, mix_factor=0.999, plot_interval=60):
        self.__output_path = pathlib.Path(output_path)
        self.__output_path.mkdir(exist_ok=True, parents=True)
        self.__output_path = self.__output_path.resolve()

        self.__mix_factor = mix_factor
        self.__plot_interval = plot_interval

        self.__processing_queue = multiprocessing.Queue()
        self.__subprocess = multiprocessing.Process(
            target=ClockReporter.__process_handler,
            args=(self.__processing_queue, str(self.__output_path)))
        self.__subprocess.daemon = True
        self.mix_factor = self.mix_factor
        self.plot_interval = self.plot_interval
        self.__subprocess.start()

    @property
    def output_path(self):
        return pathlib.Path(self.__output_path)

    @property
    def mix_factor(self):
        return self.__mix_factor

    @mix_factor.setter
    def mix_factor(self, value):
        self.__mix_factor = float(value)
        self.__processing_queue.put(
            {"cmd": "set", "name": "mix_factor", "value": self.__mix_factor})

    @property
    def plot_interval(self):
        return self.__plot_interval

    @plot_interval.setter
    def plot_interval(self, value):
        self.__plot_interval = float(value)
        self.__processing_queue.put(
            {"cmd": "set", "name": "plot_interval", "value": self.__plot_interval})

    def track(self):
        return TimeTrail(self.__processing_queue)

    def close(self):
        if self.__subprocess:
            self.__processing_queue.put({"cmd": "exit"})
            self.__processing_queue.close()
            self.__subprocess.join()
