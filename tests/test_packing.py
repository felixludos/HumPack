
from humpack import pack, unpack, json_unpack, json_pack
from _util_test import get_adict


def test_pack_tdict():
	data = get_adict()
	rec = unpack(pack(data))
	
	assert repr(data) == repr(rec)


def test_json_pack_transactionable():
	data = get_adict()
	
	s = json_pack(data)
	assert repr(json_unpack(s)) == repr(data)
	
	data.begin()
	
	data[1234] = 'element'
	assert 1234 in data
	assert 'element' == data[1234]
	
	data.abc = 123
	assert 'abc' in data
	assert data.abc == 123
	assert data['abc'] == 123
	
	data.abort()
	
	assert repr(json_unpack(s)) == repr(data)
	
	