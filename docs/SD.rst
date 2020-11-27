=================
(De)Serialization
=================

.. automodule:: ToBeGreen.SD

Backend Interface
=================

.. autofunction:: strToBytes
.. autofunction:: bytesToStr
.. autoexception:: ObeseMessageException
.. autofunction:: pascalify
.. autofunction:: depascalify
.. autofunction:: peel

Serializers
===========

.. autofunction:: _bytes_ser
.. autofunction:: _str_ser
.. autofunction:: _int_ser
.. autofunction:: _bool_ser
.. autofunction:: _float_ser
.. autofunction:: _complex_ser
.. autofunction:: _list_ser
.. autofunction:: _tuple_ser
.. autofunction:: _set_ser
.. autofunction:: _frozenset_ser
.. autofunction:: _dict_ser

Deserializers
=============

.. autofunction:: _bytes_des
.. autofunction:: _str_des
.. autofunction:: _int_des
.. autofunction:: _bool_des
.. autofunction:: _float_des
.. autofunction:: _complex_des
.. autofunction:: _list_des
.. autofunction:: _tuple_des
.. autofunction:: _set_des
.. autofunction:: _frozenset_des
.. autofunction:: _dict_des

Frontend Interface
==================

.. autodata:: serers
	:annotation: = {type: ["typename", serializer_function], ...}
.. autodata:: desers
	:annotation:  = {"typename": deserializer_function, ...}
.. autofunction:: Ser
.. autofunction:: Des

Examples
========

The following example code shows how to use the primary functions 'Ser' and
'Des'::
	
	from ToBeGreen import Ser, Des
	
	x = {
		"hi": [
			7,
			b"blob",
			{
				3,
				2,
				1,
			}
		],
		"bye": (
			frozenset({
				True,
			}),
		)
	}
	
	y = Des(Ser(x)) # It is actually this simple.
	
	assert x == y, "This should never print."

You can create your own serialization and deserialization methods and register
them for 'Ser' and 'Des' to use. The following example code shows one possible
way that one could provide an implementation for complex-valued types if such an
implementation were not provided out-of-the-box::
	
	from ToBeGreen import SD
	from ToBeGreen import serers, desers
	
	def _complex_ser(x):
		"Serialize a complex."
		return SD._float_ser(x.real) + b" " + SD._float_ser(x.imag)
	
	def _complex_des(bobj):
		"Deserialize into a complex."
		delim = bobj.index(b" ")
		return complex(
			SD._float_des(bobj[ : delim]),
			SD._float_des(bobj[delim + 1 : ])
		)
	
	serers[complex] = [complex.__name__, _complex_ser]
	desers[complex.__name__] = _complex_des

NOTE: 'Ser' and 'Des' will automatically take care of the overhead of labeling
the type of the object and specifying the length of the blob for you, so all you
have to do to serialize the object is to return an unambiguous blob for which
you can provide a deserializer.
