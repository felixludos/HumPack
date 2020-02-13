from humpack import pack, unpack, json_unpack, json_pack
from _util_test import get_tdict


def test_json_pack_transactionable():
	'''Test transactionable functionality'''
	data = get_tdict()
	
	data.q = 0
	assert 'q' in data and data.q == 0
	
	data.begin()

	assert 'q' in data and data.q == 0
	data.q = 1
	assert 'q' in data and data.q == 1
	
	data.commit()
	
	assert 'q' in data and data.q == 1
	
	data.begin()
	
	del data.q
	assert 'q' not in data
	
	data.abort()

	assert 'q' in data and data.q == 1
