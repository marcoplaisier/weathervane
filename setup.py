from setuptools import setup, find_packages

setup(
    name="weathervane",
    packages=find_packages(),
    long_description=open('README.rst', 'r').read(),
    install_requires=[
        "spidev",
        "httpx",
    ],
    entry_points={
        "console_scripts": [
            "weathervane=main:main",  # Replace `main:main` with the actual entry point
        ],
    },
    data_files=[
        ('lib/systemd/system', ['weathervane.service']),
    ],
)
