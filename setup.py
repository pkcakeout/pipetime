from distutils.core import setup

setup(
    name='pipetime',
    description='Tool to measure processing timings',
    version='1.0',
    author="Paul Konstantin Gerke",
    author_email="paul.gerke@radboudumc.nl",
    requires=["bokeh (>=1.0.4)"],
    license="MIT",
)

