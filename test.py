import tempfile
import pipetime
import time

def test_shutdown(tmp_path):
    pipe_reporter = pipetime.ClockReporter(tmp_path)
    pipe_reporter.close()


def test_value_updates(tmp_path):
    pipe_reporter = pipetime.ClockReporter(tmp_path, plot_interval=0.)
    time.sleep(1)
    print(list(pipe_reporter.output_path.iterdir()))
    assert ".html" in [f.suffix.lower() for f in pipe_reporter.output_path.iterdir()]
    pipe_reporter.close()

