"""Central store: catenae addressed on 15 bits, each with its check key.

The store has 1 to 8 blocks of 4,096 catenae (bounds of the profile). An address beyond the
installed blocks fails the selection check [B61 p.10 ; ONDE §2.2.2.3]: ``SelectionError``.
Timing (one catena per cycle) is the Data Distributor's business, not the store's.
"""

from __future__ import annotations

from gamma60 import data
from gamma60.catena import MASK15, Catena

BLOCK = 4096


class SelectionError(IndexError):
    """Address outside the installed blocks (selection check)."""


class Memory:
    def __init__(self, profile: data.Profile | None = None, blocks: int = 8) -> None:
        self.profile = profile or data.get_profile()
        if not self.profile.memory_blocks_min <= blocks <= self.profile.memory_blocks_max:
            raise ValueError(f"{blocks} blocks outside the range of profile {self.profile.name}")
        self.size = blocks * BLOCK
        zero = Catena.make(0, self.profile)
        self._cells = [zero] * self.size

    def _check(self, address: int) -> None:
        if not 0 <= address < self.size or address > MASK15:
            raise SelectionError(f"address {address} outside the store ({self.size} catenae)")

    def read(self, address: int) -> int:
        self._check(address)
        return self._cells[address].checked(self.profile)

    def write(self, address: int, value: int) -> None:
        self._check(address)
        self._cells[address] = Catena.make(value, self.profile)

    def raw(self, address: int) -> Catena:
        """Stored catena with its key, without checking (for tests and fault injection)."""
        self._check(address)
        return self._cells[address]

    def poke_raw(self, address: int, catena: Catena) -> None:
        self._check(address)
        self._cells[address] = catena
