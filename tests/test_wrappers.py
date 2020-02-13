
import numpy as np

from _util_test import get_tdict
from humpack import json_pack, json_unpack


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

