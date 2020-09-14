#!/bin/python3

# ToBeGreen is a python3 library used for (de)serialization between python data objects and blobs.
# Copyright (C) 2020 Stephen Fedele <32551324+strangeprogrammer@users.noreply.github.com>
# 
# This file is part of ToBeGreen.
# 
# ToBeGreen is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# ToBeGreen is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# and the GNU Lesser General Public License along with ToBeGreen.  If not, see
# <https://www.gnu.org/licenses/>.
# 
# Additional terms apply to this file.  Read the file 'LICENSE.txt' for
# more information.



"""Serialization and deserialization tools."""

__all__ = [
	### Backend Interface
	
	"strToBytes",
	"bytesToStr",
	"intToVLQ",
	"VLQToInt",
	"skipVLQ",
	"pascalify",
	"depascalify",
	"peel",
	
	### Serializers
	
	"_bytes_ser",
	"_str_ser",
	"_int_ser",
	"_bool_ser",
	"_list_ser",
	"_tuple_ser",
	"_set_ser",
	"_frozenset_ser",
	"_dict_ser",
	
	### Deserializers
	
	"_bytes_des",
	"_str_des",
	"_int_des",
	"_bool_des",
	"_list_des",
	"_tuple_des",
	"_set_des",
	"_frozenset_des",
	"_dict_des",
	
	### Frontend Interface
	
	"serers",
	"desers",
	"Ser",
	"Des",
]

### Notes:

# 'VLQ' is an acronym that basically means 'variable-length int'. VLQ's are used
# during the serialization and deserialization process to describe the length of
# the transmitted objects.
# More information on VLQ's can be found at:
# https://en.wikipedia.org/wiki/Variable-length_quantity

### Backend Interface

def strToBytes(s):
	"""Converts a string into its blob equivalent."""
	return bytes(str(s), "utf-8")

def bytesToStr(byteobj):
	"""Converts a blob into its string equivalent."""
	return str(bytes(byteobj), "utf-8")

def intToVLQ(n):
	"""Takes an integer and returns a blob representing its VLQ equivalent."""
	n = abs(int(n))
	result = []
	
	while True:
		result = [n & 0b01111111 | 0b10000000] + result
		n >>= 7
		
		if not 0 < n:
			break
	
	result[-1] &= 0b01111111
	return bytes(result)

def VLQToInt(blob):
	"""Takes a blob representing a VLQ and returns its integer equivalent."""
	n = 0
	while True:
		n <<= 7
		[x, blob] = [blob[0], blob[1:]]
		n += x & 0b01111111
		
		if not x & 0b10000000:
			return n

def skipVLQ(blob):
	"""Takes a blob and skips over its VLQ header."""
	while True:
		x = blob[0]
		if x & 0b10000000:
			blob = blob[1:]
		else:
			return blob[1:]

def pascalify(blob):
	"""Concatenate the length of a blob with the object itself, and return the result."""
	return intToVLQ(len(blob)) + blob

def depascalify(blob):
	"""Return the length of a blob along with EVERYTHING following said length field."""
	return [VLQToInt(blob), skipVLQ(blob)]

def peel(blob):
	"""Deconcatenate and depascalify a blob, and return it along with EVERYTHING that's left over."""
	[blength, blob] = depascalify(blob)
	return [
		blob[ : blength], # What we expect to receive given 'blength'
		blob[blength : ], # What we didn't expect to receive
	]

### Serializers

def _bytes_ser(x):
	"""Serialize a blob."""
	return bytes(x)

def _str_ser(x):
	"""Serialize a string."""
	return strToBytes(x)

def _int_ser(x):
	"""Serialize an integer."""
	return intToVLQ(x)

def _bool_ser(x):
	"""Serialize a boolean."""
	return b"\xFF" if x else b"\x00"

def _list_ser(x):
	"""Serialize a list recursively."""
	blob = b""
	for y in x:
		blob += pascalify(Ser(y))
	return blob

def _tuple_ser(x):
	"""Serialize a tuple recursively."""
	return _list_ser(x)

def _set_ser(x):
	"""Serialize a set recursively."""
	return _list_ser(x)

def _frozenset_ser(x):
	"""Serialize a frozenset recursively."""
	return _list_ser(x)

def _dict_ser(x):
	"""Serialize a dict recursively."""
	return _list_ser(map(_list_ser, x.items()))

### Deserializers

def _bytes_des(blob):
	"""Deserialize into a blob."""
	return blob

def _str_des(blob):
	"""Deserialize into a string."""
	return bytesToStr(blob)

def _int_des(blob):
	"""Deserialize into an integer."""
	return VLQToInt(blob)

def _bool_des(blob):
	"""Deserialize into a boolean."""
	return False if blob[0] == "\x00" else True

def _list_des(blob):
	"""Deserialize into a list (recursively)."""
	x = []
	while blob != b"":
		[y, blob] = peel(blob)
		x.append(Des(y))
	return x

def _tuple_des(blob):
	"""Deserialize into a tuple."""
	return tuple(_list_des(blob))

def _set_des(blob):
	"""Deserialize into a set."""
	return set(_list_des(blob))

def _frozenset_des(blob):
	"""Deserialize into a frozenset."""
	return frozenset(_list_des(blob))

def _dict_des(blob):
	"""Deserialize into a dict."""
	return dict(map(_list_des, _list_des(blob)))

### Frontend Interface

serers = {
	bytes:		["bytes",	_bytes_ser],
	str:		["str",		_str_ser],
	int:		["int",		_int_ser],
	bool:		["bool",	_bool_ser],
	list:		["list",	_list_ser],
	tuple:		["tuple",	_tuple_ser],
	set:		["set",		_set_ser],
	frozenset:	["frozenset",	_frozenset_ser],
	dict:		["dict",	_dict_ser],
}

desers = {
	"bytes":	_bytes_des,
	"str":		_str_des,
	"int":		_int_des,
	"bool":		_bool_des,
	"list":		_list_des,
	"tuple":	_tuple_des,
	"set":		_set_des,
	"frozenset":	_frozenset_des,
	"dict":		_dict_des,
}

def Ser(x):
	"""Serializes a python object into a blob."""
	
	try:
		[name, serializer] = serers[type(x)]
	except Exception:
		raise Exception("Error: object of type '" + name + "' couldn't be serialized...")
	
	return pascalify(strToBytes(name)) + pascalify(serializer(x))

def Des(blob):
	"""Deserializes a blob into a python object."""
	
	try:
		[name, blob] = peel(blob)
		deserializer = desers[bytesToStr(name)]
	except Exception:
		raise Exception("Error: object of type '" + name + "' couldn't be deserialized...")
	return deserializer(peel(blob)[0]) # We don't use 'skipVLQ' since it doesn't use the length given, while 'peel' does

### Unit Tests

import unittest
from unittest.mock import call, patch
import itertools

class testLooperMixin(unittest.TestCase):
	def loopTests(self, args, expecteds, f, extraAsserts = None):
		if extraAsserts == None:
			extraAsserts = itertools.repeat(lambda: None)
		
		for [i, [arg, expected, extraAssert]] in enumerate(zip(args, expecteds, extraAsserts)):
			with self.subTest(i = i):
				result = f(arg)
				self.assertEqual(result, expected)
				extraAssert()

class testVLQ(testLooperMixin):
	def test_intToVLQ(self):
		args = [
			0,
			55,
			127,
			128,
			129,
			246537,
		]
		
		expecteds = [
			b"\x00",
			b"\x37",
			b"\x7F",
			b"\x81\x00",
			b"\x81\x01",
			b"\x8F\x86\x09",
		]
		
		self.loopTests(args, expecteds, intToVLQ)
	
	def test_VLQToInt(self):
		args = [
			b"\x00garbage0",
			b"\x37garbage1",
			b"\x7Fgarbage2",
			b"\x81\x00garbage3",
			b"\x81\x01garbage4",
			b"\x8F\x86\x09garbage5",
		]
		
		expecteds = [
			0,
			55,
			127,
			128,
			129,
			246537,
		]
		
		self.loopTests(args, expecteds, VLQToInt)
	
	def test_skipVLQ(self):
		args = [
			b"\x00garbage0",
			b"\x37garbage1",
			b"\x7Fgarbage2",
			b"\x81\x00garbage3",
			b"\x81\x01garbage4",
			b"\x8F\x86\x09garbage5",
		]
		
		expecteds = [
			b"garbage0",
			b"garbage1",
			b"garbage2",
			b"garbage3",
			b"garbage4",
			b"garbage5",
		]
		
		self.loopTests(args, expecteds, skipVLQ)

class testSerializers(testLooperMixin):
	def test_bytes(self):
		arg = b"lwiherkjtghjfd"
		expected = b"lwiherkjtghjfd"
		result = _bytes_ser(arg)
		self.assertEqual(result, expected)
	
	# def test_str(self): # Too simple to write a test for as of now (except maybe the part where it uses 'utf-8', which doesn't encode arbitrary strings)
	
	# def test_int(self): # Unessecary since we've already tested 'intToVLQ' and 'VLQToInt' earlier
	
	# def test_bool(self): # Too simple to write a test for as of now
	
	@patch(__name__ + ".Ser")
	def test_list(self, notSer):
		notSer.side_effect = [
			b"\x03int\x01\x05",
			
			b"\x03str\x03bee",
			
			b"\x04list\x09" + \
				b"\x08\x03str\x03bee",
				
			b"\x03int\x01\x05",
			b"\x03str\x02hi",
			
			b"\x03int\x01\x05",
			b"\x04list\x09" + \
				b"\x08\x03str\x03bee",
			b"\x03str\x02hi",
		]
		
		args = [
			[],
			[5],
			["bee"],
			[["bee"]],
			[5, "hi"],
			[5, ["bee"], "hi"],
		]
		
		expecteds = [
			b"",
			
			b"\x06\x03int\x01\x05",
			
			b"\x08\x03str\x03bee",
			
			b"\x0F\x04list\x09" + \
				b"\x08\x03str\x03bee",
			
			b"\x06\x03int\x01\x05" + \
			b"\x07\x03str\x02hi",
			
			b"\x06\x03int\x01\x05" + \
			b"\x0F\x04list\x09" + \
				b"\x08\x03str\x03bee" + \
			b"\x07\x03str\x02hi",
		]
		
		extraAsserts = [
			lambda: notSer.assert_has_calls([call(5)]),
			lambda: notSer.assert_has_calls([call("bee")]),
			lambda: notSer.assert_has_calls([call(["bee"])]),
			lambda: notSer.assert_has_calls([call(5, "hi")]),
			lambda: notSer.assert_has_calls([call(5, ["bee"], "hi")]),
		]
		
		self.loopTests(args, expecteds, _list_ser)
	
	# def test_tuple(self): # Since '_tuple_ser' is just a call to '_list_ser', it is redundant
	
	# def test_set(self): # Since '_set_ser' is just a call to '_list_ser', it is redundant
	
	# def test_frozenset(self): # Since '_frozenset_ser' is just a call to '_list_ser', it is redundant
	
	# @patch(__name__ + "._list_ser")
	# def test_dict(self, notListSer): # I could test this, but it's too simple for me to bother

class testDeserializers(testLooperMixin):
	def test_bytes(self):
		arg = b"lwiherkjtghjfd"
		expected = b"lwiherkjtghjfd"
		result = _bytes_des(arg)
		self.assertEqual(result, expected)
	
	# def test_str(self): # Too simple to write a test for as of now (except maybe the part where it uses 'utf-8', which doesn't encode arbitrary strings)
	
	# def test_int(self): # Unessecary since we've already tested 'intToVLQ' and 'VLQToInt' earlier
	
	# def test_bool(self): # Too simple to write a test for as of now
	
	@patch(__name__ + ".Des")
	def test_list(self, notDes):
		notDes.side_effect = [
			5,
			"bee",
			["bee"],
			5, "hi",
			5, ["bee"], "hi",
		]
		
		args = [
			b"",
			
			b"\x06\x03int\x01\x05",
			
			b"\x08\x03str\x03bee",
			
			b"\x0F\x04list\x09" + \
				b"\x08\x03str\x03bee",
			
			b"\x06\x03int\x01\x05" + \
			b"\x07\x03str\x02hi",
			
			b"\x06\x03int\x01\x05" + \
			b"\x0F\x04list\x09" + \
				b"\x08\x03str\x03bee" + \
			b"\x07\x03str\x02hi",
		]
		
		expecteds = [
			[],
			[5],
			["bee"],
			[["bee"]],
			[5, "hi"],
			[5, ["bee"], "hi"],
		]
		
		extraAsserts = [
			lambda: notDes.assert_has_calls([
				call(b"\x03int\x01\x05")
			]),
			lambda: notDes.assert_has_calls([
				call(b"\x03str\x03bee")
			]),
			lambda: notDes.assert_has_calls([
				call(b"\x04list\x09" + \
					b"\x08\x03str\x03bee"),
			]),
			lambda: notDes.assert_has_calls([
				call(b"\x03int\x01\x05"),
				call(b"\x03str\x02hi"),
			]),
			lambda: notDes.assert_has_calls([
				call(b"\x03int\x01\x05"),
				call(b"\x04list\x09" + \
					b"\x08\x03str\x03bee"),
				call(b"\x03str\x02hi"),
			]),
		]
		
		self.loopTests(args, expecteds, _list_des)
	
	# def test_tuple(self): # Since '_tuple_des' is just a call to '_list_des', it is redundant
	
	# def test_set(self): # Since '_set_des' is just a call to '_list_des', it is redundant
	
	# def test_frozenset(self): # Since '_frozenset_des' is just a call to '_list_des', it is redundant
	
	# @patch(__name__ + "._list_des")
	# def test_dict(self, notListDes): # I could test this, but it's too simple for me to bother

if __name__ == "__main__":
	unittest.main()
