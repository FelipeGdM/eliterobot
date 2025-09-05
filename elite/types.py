from dataclasses import dataclass
from typing import Any, cast


@dataclass
class CmdResponse:
    """Representation of robot responses"""

    success: bool
    result: Any
    id: str

    def __bool__(self):
        if not isinstance(self.result, bool):
            raise TypeError("Trying to auto convert to bool a non bool value")
        return self.success and self.result
