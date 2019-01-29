from __future__ import print_function

import pipetime
import time

def test_shutdown(tmp_path):
    pipe_reporter = pipetime.ClockReporter(tmp_path)
    pipe_reporter.close()


def test_value_updates(tmp_path):
    pipe_reporter = pipetime.ClockReporter(tmp_path, plot_interval=0.)

    timetracker = pipe_reporter.track()
    timetracker.time("step1")
    time.sleep(.2)
    timetracker.time("step2")

    pipe_reporter.mix_factor = 0.5

    time.sleep(.3)

    timetracker = pipe_reporter.track()
    time.sleep(.05)
    timetracker.time("step1")
    time.sleep(.1)
    timetracker.time("step2")

    time.sleep(.5)
    print(list(pipe_reporter.output_path.iterdir()))
    assert ".html" in [f.suffix.lower() for f in pipe_reporter.output_path.iterdir()]
    pipe_reporter.close()


def test_saturate_input_channel(tmp_path):
    pipe_reporter = pipetime.ClockReporter(tmp_path, plot_interval=0.1)

    try:
        start_time = time.time()
        while time.time() - start_time < 1.0:
            timetracker = pipe_reporter.track()
            timetracker.time("step1")
            timetracker.time("step2")

            if time.time() - start_time > 0.2:
                assert ".html" in [f.suffix.lower() for f in pipe_reporter.output_path.iterdir()]
    finally:
        pipe_reporter.close()
