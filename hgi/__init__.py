"""HGI — an attached associative memory for agent loops.

The package is organised by the two passes of the loop and the organs they
share:

- ``types``       every record kind, declared once as pydantic models
- ``registry``    the closed vocabularies, ports, bars, cap and lens fans
- ``store``       read/write, id minting, the committer, the pre-admission tier
- ``index``       regenerated projections (hook-major index, fires, triggers)
- ``lint``        the floor; its docstring is the home of the check list
- ``model``       the frozen model behind every role, traced through Weave
- ``boot``        the forward pass opens (§ 8.1 of the specification)
- ``evaluate``    the oracle scores the pass and fires latches (§ 9.2)
- ``close``       the forward pass closes and produces the backward pass's inputs (§ 8.6)
- ``consolidate`` the backward pass under separation of powers (§ 10)
- ``cli``         ``hgi boot | evaluate | close | consolidate | lint | index | lineage``
"""

__version__ = "0.1.0"
