
import numpy as np

from _util_test import get_tdict
from humpack import json_pack, json_unpack
from humpack.wrappers import Array

def test_numpy_wrapper():
	
	x = Array(np.random.randn(4).astype(object))
	
	x[0] = get_tdict()
	x[1] = 0
	
	assert x[1] == 0
	
	x.begin()
	
	x[0].arr = x
	x[1] = 10
	
	assert 'arr' in x[0]
	assert len(x[0].arr) == len(x)
	assert x[1] == 10
	
	assert repr(x) == repr(json_unpack(json_pack(x)))
	
	x.abort()
	
	assert x[1] == 0
	assert 'arr' not in x[0]
	assert repr(json_unpack(json_pack(x))) == repr(x)
	

def test_numpy_arrays():
	x = np.random.randn(10)
	p = json_pack(x)
	c = json_unpack(p)
	
	assert (c-x).sum() == 0


def test_complex_array():
	x = np.arange(3).astype(object)
	
	x[0] = get_tdict()
	
	p = json_pack(x)
	c = json_unpack(p)
	
	assert repr(x) == repr(c)

