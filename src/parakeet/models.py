from enum import Enum
from typing import NamedTuple

class GPTModel(Enum):
    GPT_4O = "gpt-4o"
    GPT_4O_MINI = "gpt-4o-mini"
    GPT_3_5_TURBO = "gpt-3.5-turbo"

class BotQuery(NamedTuple):
    message: str
    model: GPTModel

    def unpack(self) -> tuple[str, GPTModel]:
        return self.message, self.model