
from typing import Any, Union, Dict, List, Set, Tuple, NoReturn, ClassVar, TextIO, Callable

import base64
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from collections import OrderedDict

from .packing import json_pack, json_unpack, SERIALIZABLE, PACKED, JSONABLE
from .errors import WrongKeyError, UnknownUserError, UnknownActionError, InsufficientPermissionsError
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


class Permission_Handler:  # TODO: make transactionable, actually just move to humpack
	
	def __init__(self, power_hierarchy={}, default_roles=[], god=None):
		
		self.god = god  # separate role that can't be modified by clients
		
		self.users = OrderedDict()  # user -> roles
		self.powers = OrderedDict()  # user -> power
		
		self._power_hierarchy = OrderedDict()  # role -> power
		self.roles = OrderedDict()  # role -> users
		self.update_roles(**power_hierarchy)
		
		self.default_roles = [role for role in default_roles if role in self.roles]  # for new users
		
		self.permissions = OrderedDict()  # action -> roles
		self.actions = OrderedDict()  # action -> power
	
	def _update_consistency(self, users=[], roles=[]):
		
		if not (len(users) or len(roles)):
			users = list(self.users.keys())
			roles = list(self.roles.keys())
		
		for user in users:
			for role, usrs in self.roles.items():
				if role not in self.users[user] and user in usrs:
					self.users[user].add(role)
				elif role in self.users[user] and user not in usrs:
					self.users[user].remove(role)
		
		for role in roles:
			for user, rls in self.users.items():
				if user not in self.roles[role] and role in rls:
					self.roles[role].add(user)
				elif user in self.roles[role] and role not in rls:
					self.roles[role].remove(role)
	
	def __contains__(self, user):
		return self.contains_user(user)
	
	def contains_user(self, user):
		return user in self.users or user in self.powers
	
	def contains_action(self, action):
		return action in self.actions or action in self.permissions
	
	def _update_role(self, name, power):
		if name not in self.roles:
			self.roles[name] = set()
		self._power_hierarchy[name] = power
	
	def update_role(self, role, power):
		self._update_role(role, power)
		self._update_consistency(role=[role])
	
	def update_roles(self, **roles):
		for name, power in roles.items():
			self._update_role(name, power)
		self._update_consistency(role=roles)
	
	def update_user(self, user, *roles, power=None):
		
		if power is not None:
			self.powers[user] = power
		
		if len(roles):
			if user not in self.users:
				self.users[user] = set()
			self.users[user].update(roles)
	
	def new_user(self, user, *roles, power=None):
		
		roles = set(roles)
		roles.update(self.default_roles)
		
		self.update_user(user, *roles, power=power)
	
	def set_user(self, user, *roles, power=None):
		
		if power is None and user in self.powers:
			del self.powers[user]
		
		self.update_user(user, *roles, power=power)
	
	def remove_user(self, user):
		
		if user in self.users:
			del self.users[user]
		
		if user in self.powers:
			del self.powers[user]
	
	def update_action(self, action, *roles, power=None):
		
		if power is not None:
			self.actions[action] = power
		
		if len(roles):
			if action not in self.permissions:
				self.permissions[action] = set()
			self.permissions[action].update(roles)
	
	def new_action(self, action, *roles, power=None):
		self.update_action(action, *roles, power=power)
	
	def set_action(self, action, *roles, power=None):
		
		if power is None and action in self.actions:
			del self.actions[action]
		
		self.update_action(action, *roles, power=power)
	
	def remove_action(self, action):
		
		if action in self.actions:
			del self.actions[action]
		
		if action in self.permissions:
			del self.permissions[action]
	
	def validate(self, user, action=None):
		
		if user == self.god:
			return user
		
		if self.contains_user(user):
			raise UnknownUserError(user)
		
		if action is None:
			return user
		
		if not self.contains_action(action):
			raise UnknownActionError(action)
		
		if user in self.users and action in self.permissions \
				and len(self.users[user].intersection(self.permissions[action])):
			return user
		
		if user in self.powers and action in self.actions \
				and self.powers[user] >= self.actions[action]:
			return user
		
		if user in self.users and action in self.actions:
			power = max(self._power_hierarchy.get(role, 0) for role in self.users[user])
			if power >= self.actions[action]:
				return user
		
		if user in self.powers and action in self.permissions:
			req = min(self._power_hierarchy.get(role, 0) for role in self.permissions[action])
			if self.powers[user] >= req:
				return user
		
		raise InsufficientPermissionsError(user, action)


