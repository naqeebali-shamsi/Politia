from enum import StrEnum


class Chamber(StrEnum):
    LOK_SABHA = "Lok Sabha"
    RAJYA_SABHA = "Rajya Sabha"


class ElectionResult(StrEnum):
    WON = "Won"
    LOST = "Lost"


class ParseStatus(StrEnum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL = "partial"


class ConstituencyType(StrEnum):
    GENERAL = "General"
    SC = "SC"
    ST = "ST"
