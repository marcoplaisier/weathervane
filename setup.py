from setuptools import setup


def readme():
    with open('README.rst') as f:
        return f.read()


setup(name='weathervane',
      version='0.2',
      description='Collect weather data from public source(s) and display on 32-LED weathervane',
      url='http://github.com/marcofinalist/weathervane',
      author='Marco Plaisier',
      author_email='m.plaisier@gmail.com',
      license='MIT',
      packages=['weathervane'],
      zip_safe=False,
      classifiers=[
          'Development Status :: 2 - Pre-Alpha',
          'Natural Language :: English',
          'Operating System :: Linux',
          'Programming Language :: Python :: 2.7',
          'Topic :: Home Automation',
      ],
      requires=['BeautifulSoup', 'mock']
      )
