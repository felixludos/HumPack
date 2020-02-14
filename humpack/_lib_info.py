


long_name = 'HumPack'
name = 'humpack'

version = '0.1.1'

description = 'Human Readable Object Serialization and more'

url = 'https://github.com/fleeb24/HumPack'

author = 'Felix Leeb'
author_email = 'felix.leeb@hotmail.com'

license = 'GPL3'

packages = ['humpack']

# Automatically get list of requirements from requirements.txt
import os
path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
install_requires = []
if 'requirements.txt' not in os.listdir(path):
    print('WARNING: no requirements.txt found')
    install_requires = ['wrapt', 'cryptography']
    # raise FileNotFoundError('requirements.txt not found, this usually happens if part of this library is missing')
else:
    with open(os.path.join(path, 'requirements.txt'), 'r') as f:
        install_requires = [pk[:-1] for pk in f.readlines() if len(pk)]

