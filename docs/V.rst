============
Verification
============

.. automodule:: ToBeGreen.V

Backend Interface
=================

.. autoclass:: VERIFYABLE
.. autoclass:: OFLENGTH
.. autoclass:: CUSTOM

Pre-Made Specifications
=======================

.. autoclass:: SUM
.. autoclass:: PRODUCT
.. autoclass:: ITERABLE
.. autoclass:: LIST
.. autoclass:: TUPLE
.. autoclass:: SET
.. autoclass:: FROZENSET
.. autoclass:: DICT

Frontend Interface
==================

.. autofunction:: Ver

Examples
========

The following example code shows how to use various parts of this module in
order to verify object types::
	
	from ToBeGreen import V, Ver
	
	obj = [
		{frozenset({1, "bleh", 3}):	58},
		{"second":			83 + 95.2j},
		{"third":			83820 + 0j},
		{frozenset({888, (1, 2, 3)}):	27},
	]
	
	spec = V.LIST(
		V.DICT(
			V.SUM(
				V.PRODUCT(
					frozenset, # This frozenset can contain literally anything since the verifier will not recurse into it (as opposed to 'V.FROZENSET', into which it will recurse)
					int,
				),
				V.PRODUCT(
					str,
					complex,
				),
			),
			length = 1,
		),
		minlength = 3,
		maxlength = 6,
	)
	
	assert Ver(obj, spec), "This should never print."
