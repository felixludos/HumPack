from setuptools import setup

setup(name='humpack',
      version='0.1',
      description='Human Readable Object Serialization',
      url='https://github.com/fleeb24/HumPack',
      author='Felix Leeb',
      author_email='fleeb@tuebingen.mpg.edu',
      license='MIT',
      packages=['humpack'],
      install_requires=[
            'wrapt',
      ],
      zip_safe=False)