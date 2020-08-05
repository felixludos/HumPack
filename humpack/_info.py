
name = 'humpack'
long_name = 'HumPack'

version = '0.3'

url = 'https://github.com/felixludos/HumPack'

description = 'Human Readable Object Serialization and more'

author = 'Felix Leeb'
author_email = 'felixludos.info@gmail.com'

license = 'GPL3'

readme = 'README.rst'

packages = ['humpack']

import os
try:
	with open(os.path.join(os.path.abspath(os.path.dirname(os.path.dirname(__file__))), 'requirements.txt'), 'r') as f:
		install_requires = f.readlines()
except:
	install_requires = ['wrapt', 'cryptography']
del os

