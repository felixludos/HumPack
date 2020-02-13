
from typing import Any, Union, Dict, List, Set, Tuple, NoReturn, ClassVar, TextIO, Callable

import base64
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from .packing import json_pack, json_unpack, SERIALIZABLE, PACKED, JSONABLE
from .errors import WrongKeyError
from cryptography.fernet import Fernet, InvalidToken, InvalidSignature
from crypt import crypt, mksalt
from getpass import getpass
# from hmac import compare_digest


_master_salt = '6FwLrxJb5mTPVwthumpackMASTERsalt'

def format_key(hsh: Union[str, bytes]) -> bytes:
	'''
	Reformat a hash (can be str or bytes)
	
	:param hsh: hash to be reformatted
	:return: a key which can be used for decrypting the data
	'''
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

def secure_key(word: str, salt: str = None) -> str:
	'''
	Get a hash from the raw text password
	
	:param word: raw text password
	:param salt: random salt to seed the hash computation
	:return: hash of the password
	'''
	if salt is None:
		salt = _master_salt
	hsh = crypt(word, salt)
	return hsh

def prompt_password_hash(salt: str = None) -> str:
	'''
	Get the hash of a password which is entered by the user in a prompt
	
	:param salt: random salt for hash computation
	:return: hash of the entered password
	'''
	if salt is None:
		salt = _master_salt
	hsh = secure_key(getpass(), salt=salt)
	return hsh



def encrypt(data: bytes, hsh: Union[str, bytes] = None) -> bytes:
	'''
	Encrypt the data from a provided hash (or prompt for a password if no hash is provided)
	
	:param data: bytes to be encrypted
	:param hsh: hash used as key to encrypt
	:return: encrypted data bytes
	'''
	if hsh is None:
		hsh = prompt_password_hash()
	key = format_key(hsh)
	f = Fernet(key)
	return f.encrypt(data)

def decrypt(data: bytes, hsh: Union[str, bytes] = None) -> bytes:
	'''
	Decrypt data with provided hash (or prompt for a password to compute hash if no hash is provided)
	
	:param data: encrypted bytes that should be decrypted
	:param hsh: hash of a password to be used as a key to decrypt (obviously, must be the same as was used to encrypt)
	:return: the decrypted data, or a WrongKeyError if the key failed
	'''
	if hsh is None:
		hsh = prompt_password_hash()
	key = format_key(hsh)
	f = Fernet(key)
	try:
		return f.decrypt(data)
	except (InvalidToken, InvalidSignature):
		pass
	raise WrongKeyError



def secure_pack(obj: SERIALIZABLE, hsh: Union[str, bytes] = None,
                meta: Dict[str,JSONABLE] = None, include_timestamp:bool = False) -> bytes:
	'''
	Pack the object and encrypt it using the provided hash (prompt user for password if none is provided)
	
	:param obj: object to be packed
	:param hsh: hash used as key to encrypt
	:param meta: meta information to store with the packed `obj`
	:param include_timestamp: include timestamp in meta info
	:return: encrypted bytes
	'''
	data = json_pack(obj, meta=meta, include_timestamp=include_timestamp)
	data = data.encode('latin1')

	if hsh is None:
		hsh = prompt_password_hash()

	return encrypt(data, hsh)

def secure_unpack(data: bytes, hsh: Union[str, bytes] = None,
                  return_meta: bool = False) -> SERIALIZABLE:
	'''
	Decrypt `data` and unpack to recover the original object using the provided hash as a key
	
	:param data: encrypted bytes
	:param hsh: hash to be used as a key to decrypt (prompt user, if not provided)
	:param return_meta: include meta info in output
	:return: decrypted and unpacked object, possibly including the meta info
	'''
	if hsh is None:
		hsh = prompt_password_hash()
	
	data = decrypt(data, hsh).decode('latin1')
	data = json_unpack(data, return_meta=return_meta)

	return data





