import pathlib
import multiprocessing
import queue
import time
from collections import OrderedDict

import bokeh.plotting
import bokeh.io


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
    def create_plot(history, path, timestamp, timing_values, timing_counts):
        if not history:
            history = {
                "timestamps": [],
                "values": OrderedDict(),
                "counts": OrderedDict()
            }

        init_len = len(history["timestamps"])

        def append_values(value_hist, new_values):
            for k, value in new_values.items():
                values = value_hist.get(k, [None] * init_len)
                values.append(value)
                yield (k, values)

        history = {
            "timestamps": history["timestamps"] + [timestamp],
            "values": OrderedDict(
                **dict(append_values(history["values"], timing_values))),
            "counts": OrderedDict(
                **dict(append_values(history["counts"], timing_values))),
        }

        if len(history["timestamps"]) > 1:
            color_rotation = (
                "#000000",
                "#FF0000",
                "#00FF00",
                "#0000FF",
                "#FF00FF",
                "#00FFFF",
                "#FFFF00",
            )

            timings_figure = bokeh.plotting.figure(
                title="Timings", plot_width=800, plot_height=600)
            for i, (k, values) in enumerate(history["values"].items()):
                timings_figure.line(
                    history["timestamps"],
                    values,
                    legend=k,
                    color=color_rotation[i % len(color_rotation)])

            bokeh.io.save(
                timings_figure,
                filename=pathlib.Path(path) / "timings.html",
                title="Timings")

        return history

    @staticmethod
    def __process_handler(rqueue: multiprocessing.Queue, path):
        history_data = None

        timing_values = {}
        timing_counts = {}

        mix_factor = 0
        plot_interval = 0

        start_time = time.time()
        plot_timeout_start = start_time
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

            if cmd is None:
                # Cycle
                if time.time() - plot_timeout_start > plot_interval:
                    plot_timeout_start = time.time()
                    history_data = ClockReporter.create_plot(
                        history_data, path, time.time() - start_time, timing_values, timing_counts)
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

    def __init__(self, output_path, mix_factor=0.95, plot_interval=60):
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
