from setuptools import setup
# from humpack import _lib_info as info
import humpack._lib_info as info

setup(name=info.name,
      version=info.version,
      description=info.description,
      url=info.url,
      author=info.author,
      author_email=info.author_email,
      license=info.license,
      packages=info.packages,
      install_requires=info.install_requires,
      zip_safe=False)