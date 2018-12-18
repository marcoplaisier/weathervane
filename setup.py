import sys
import getpass
import os

import requests
from setuptools import setup, find_packages
from setuptools.command.install import install
from werkzeug.security import generate_password_hash


def long_description():
    with open('README.rst') as f:
        return f.read()


class NotInstalledError(Exception):
    pass


class Install(install):
    def run(self):
        operating_system = os.environ.get('OS', 'unknown')
        if 'windows' in operating_system.lower():
            sys.exit('Cannot install on Windows')
        self.install_wiring_pi()
        self.get_and_store_temp_credentials()
        self.create_key_pair()
        self.create_device_on_gcp()

    @staticmethod
    def get_and_store_temp_credentials():
        url = 'https://europe-west1-weathervane-207309.cloudfunctions.net/retrieve-credentials'
        password = getpass.getpass()

        body = {'hash': generate_password_hash(password)}
        r = requests.get(url, params=body)
        with open('secrets.json', 'w') as secrets_file:
            secrets_file.write(r.text)

    @staticmethod
    def install_wiring_pi():
        print('Installing WiringPi (if required)...')
        if os.system('gpio -v') > 0:
            os.system('git clone git://git.drogon.net/wiringPi')
            os.chdir('/home/pi/wiringPi')
            os.system('./build')
        else:
            print('WiringPi already installed.')

        if os.system('gpio -v') > 0:
            raise NotInstalledError('Failed to install WiringPi')

    @staticmethod
    def create_key_pair():
        private_key_file = 'rsa_private.pem'
        public_key_file = 'rsa_public.pem'
        os.system('openssl genrsa -out {private_key_file} 2048'.format(private_key_file=private_key_file))
        os.system('openssl rsa -in {private_key_file} -pubout -out {public_key_file}'.format(
            private_key_file=private_key_file, public_key_file=public_key_file))
        return [private_key_file, public_key_file]

    @staticmethod
    def create_device_on_gcp(service_account_json, project_id, cloud_region, registry_id, device_id, public_key_file):
        """Create a new device with the given id, using ES256 for authentication."""
        registry_name = 'projects/{}/locations/{}/registries/{}'.format(project_id, cloud_region, registry_id)

        client = get_client(service_account_json)
        with open(public_key_file) as f:
            public_key = f.read()

        # Note: You can have multiple credentials associated with a device.
        device_template = {
            'id': device_id,
            'credentials': [{
                'publicKey': {
                    'format': 'ES256_PEM',
                    'key': public_key
                }
            }]
        }

        devices = client.projects().locations().registries().devices()
        return devices.create(parent=registry_name, body=device_template).execute()


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
      entry_points={
          'console_scripts': [
              'wv = main:run'
          ]
      },
      cmdclass={
          'install': Install
      })
