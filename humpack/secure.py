
import base64
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from .packing import json_pack, json_unpack
from .errors import WrongKeyError
from cryptography.fernet import Fernet, InvalidToken, InvalidSignature
from crypt import crypt, mksalt
from getpass import getpass
# from hmac import compare_digest


_master_salt = '6FwLrxJb5mTPVwthumpackMASTERsalt'

def format_key(hsh):
	if isinstance(hsh, str):
		hsh = hsh.encode('latin1')
	
	kdf = PBKDF2HMAC(
		algorithm=hashes.SHA256(),
		length=32,
		salt=_master_salt.encode('latin1'),
		iterations=100000,
		backend=default_backend(),
	)
	return base64.urlsafe_b64encode(kdf.derive(hsh))

def secure_key(word, salt=None):
	if salt is None:
		salt = _master_salt
	hsh = crypt(word, salt)
	return hsh

def prompt_password_hash(salt=None):
	if salt is None:
		salt = _master_salt
	hsh = secure_key(getpass(), salt=salt)
	return hsh



def encrypt(data, hsh=None):
	if hsh is None:
		hsh = prompt_password_hash()
	key = format_key(hsh)
	f = Fernet(key)
	return f.encrypt(data)

def decrypt(data, hsh=None):
	if hsh is None:
		hsh = prompt_password_hash()
	key = format_key(hsh)
	f = Fernet(key)
	try:
		return f.decrypt(data)
	except (InvalidToken, InvalidSignature):
		pass
	raise WrongKeyError



def secure_pack(obj, hsh=None, include_timestamp=False):
	data = json_pack(obj, include_timestamp=include_timestamp)
	data = data.encode('latin1')

	if hsh is None:
		hsh = prompt_password_hash()

	return encrypt(data, hsh)

def secure_unpack(data, hsh=None, return_meta=False):
	if hsh is None:
		hsh = prompt_password_hash()
	
	data = decrypt(data, hsh).decode('latin1')
	data = json_unpack(data, return_meta=return_meta)

	return data





