from setuptools import find_packages, setup


def long_description():
    with open("README.rst") as f:
        return f.read()


setup(
    name="weathervane",
    version="0.3",
    description="Collect weather data from public source(s) and display on 32-LED weathervane",
    long_description=long_description(),
    long_description_content_type="text/x-rst",
    url="https://github.com/marcoplaisier/weathervane",
    author="Marco Plaisier",
    author_email="m.plaisier@gmail.com",
    license="MIT",
    packages=find_packages(),
    zip_safe=False,
    classifiers=[
        "Natural Language :: English",
        "Programming Language :: Python :: 3",
        "Topic :: Home Automation",
    ],
    entry_points={"console_scripts": ["wv = main:run"]},
)
