import tempfile
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

