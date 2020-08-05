
from _util_test import get_adict
import humpack.secure as scr


def test_format_key_ans():
	hash = 'test'
	ans = b'zvD0UaW17E3eDz9U7sdW9K1_Xs7Ctwgz9LQiyEzPtxM='
	b = scr.format_key(hash)
	assert b == ans

def test_format_key():
	hash = 'test'
	b = scr.format_key(hash)
	assert len(b) == 44

def test_secure_key():
	hash = 'test'
	ans = 'salSp1wOPp6fk'
	
	salt = 'salt'

	assert scr.secure_key(hash, salt) == ans


def test_encryption():

	data = b'aslkjqtest_encryption()2\4awsef'
	hsh = 'test'
	
	x = scr.encrypt(data, hsh)
	rec = scr.decrypt(x, hsh)
	
	assert data == rec
	

def test_secure_pack():
	
	hsh = 'test'
	
	data = get_adict()
	b = scr.secure_pack(data, hsh=hsh)
	rec = scr.secure_unpack(b, hsh=hsh)
	
	assert repr(data) == repr(rec)
	
