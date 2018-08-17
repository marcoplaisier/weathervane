import os
import sys

from setuptools import setup, find_packages, Command
from setuptools.command.install import install


def long_description():
    with open('README.rst') as f:
        return f.read()


class Run(Command):
    def run(self):
        import main
        main.run()


class Install(install):
    def run(self):
        operating_system = os.environ.get('OS', 'unknown')
        if 'windows' in operating_system.lower():
            sys.exit('Cannot install on Windows')
        print('Installing WiringPi (if required)...')
        if os.system('gpio -v') > 0:
            os.system('git clone git://git.drogon.net/wiringPi')
            os.chdir('/home/pi/wiringPi')
            os.system('./build')
        else:
            print('WiringPi already installed.')


setup(name='weathervane',
      version='0.3',
      description='Collect weather data from public source(s) and display on 32-LED weathervane',
      long_description=long_description(),
      long_description_content_type='text/x-rst',
      url='http://github.com/marcoplaisier/weathervane',
      author='Marco Plaisier',
      author_email='m.plaisier@gmail.com',
      license='MIT',
      packages=find_packages(),
      zip_safe=False,
      classifiers=[
          'Natural Language :: English',
          'Programming Language :: Python :: 3',
          'Topic :: Home Automation'
      ],
      cmdclass={'install': Install, 'run': Run}
      )
