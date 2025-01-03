# enums.py
from enum import Enum

class NodeType(Enum):
    RUNTIME = "runtime"
    MASTER = "master"
    CONFIG = "config"

class UpgradeType(Enum):
    OVERWRITE = "overwrite"
    DONT_OVERWRITE = "dont_overwrite"
    DONT_USE = "dont_use"