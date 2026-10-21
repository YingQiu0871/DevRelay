"""v0.4-A local HTTP control API.

The package is an adapter: it exposes the accepted DevRelay read surfaces over
loopback HTTP with an explicit local session boundary.  It never implements
orchestration, provider transport, or configuration policy of its own.
"""

from __future__ import annotations
