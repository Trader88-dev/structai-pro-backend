"""
Matériaux béton et acier — EC2 et BAEL 91
"""

from dataclasses import dataclass


@dataclass
class Beton:
    classe: str
    fck: float
    fcd_ec2: float = 0.0
    fcd_bael: float = 0.0
    Ecm: float = 0.0
    fctm: float = 0.0

    def __post_init__(self):
        self.fcd_ec2  = round(1.0 * self.fck / 1.5, 2)
        self.fcd_bael = round(0.85 * self.fck / 1.5, 2)
        self.Ecm      = round(22 * ((self.fck / 10 + 8) ** 0.3), 1)
        self.fctm     = round(0.30 * self.fck ** (2/3), 2)


@dataclass
class Acier:
    nuance: str
    fyk: float
    fyd_ec2: float = 0.0
    fyd_bael: float = 0.0
    Es: float = 200000.0

    def __post_init__(self):
        self.fyd_ec2  = round(self.fyk / 1.15, 2)
        self.fyd_bael = round(self.fyk / 1.15, 2)


BETONS = {
    "C20/25": Beton("C20/25", 20),
    "C25/30": Beton("C25/30", 25),
    "C30/37": Beton("C30/37", 30),
    "C35/45": Beton("C35/45", 35),
    "C40/50": Beton("C40/50", 40),
}

ACIERS = {
    "B500B":  Acier("B500B",  500),
    "B500A":  Acier("B500A",  500),
    "FeE400": Acier("FeE400", 400),
    "HA400":  Acier("HA400",  400),
    "HA500":  Acier("HA500",  500),
    "HA520":  Acier("HA520",  520),
}

ENROBAGES = {
    "XC1": 20,
    "XC2": 25,
    "XC3": 30,
    "XC4": 35,
    "XS1": 40,
}
