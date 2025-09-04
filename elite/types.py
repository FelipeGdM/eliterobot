from dataclasses import dataclass
from typing import Any


@dataclass
class CmdResponse:
    """Representation of robot responses"""

    success: bool
    result: Any
    id: str

    def __bool__(self):
        return self.success
