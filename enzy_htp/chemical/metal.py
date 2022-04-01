"""Stores mappers and definitions for different types of metals often found in PDBs.

Author: Qianzhen (QZ) Shao <qianzhen.shao@vanderbilt.edu>
Author: Chris Jurich <chris.jurich@vanderbilt.edu>
"""

from typing import Dict

METAL_MAPPER: Dict[str, str] = {
    "LI": "Li",
    "NA": "Na",
    "Na+": "Na",
    "K": "K",
    "K+": "K",
    "RB": "Rb",
    "CS": "Cs",
    "MG": "Mg",
    "TL": "Tl",
    "CU": "Cu",
    "AG": "Ag",
    "BE": "Be",
    "NI": "Ni",
    "PT": "Pt",
    "ZN": "Zn",
    "CO": "Co",
    "PD": "Pd",
    "CR": "Cr",
    "FE": "Fe",
    "V": "V",
    "MN": "Mn",
    "HG": "Hg",
    "CD": "Cd",
    "YB": "Yb",
    "CA": "Ca", 
	"SN": "Sn",
    "PB": "Pb",
    "EU": "Eu",
    "SR": "Sr",
    "SM": "Sm",
    "BA": "Ba",
    "RA": "Ra",
    "AL": "Al",
    "IN": "In",
    "Y": "Y",
    "LA": "La",
    "CE": "Ce",
    "PR": "Pr",
    "ND": "Nd",
    "GD": "Gd",
    "TB": "Tb",
    "DY": "Dy",
    "ER": "Er",
    "TM": "Tm",
    "LU": "Lu",
    "HF": "Hf",
    "ZR": "Zr",
    "U": "U",
    "PU": "Pu",
    "TH": "Th",
}

METAL_CENTER_MAP : Dict[str,str] = {
    "MG": "Mg",
    "TL": "Tl",
    "CU": "Cu",
    "AG": "Ag",
    "BE": "Be",
    "NI": "Ni",
    "PT": "Pt",
    "ZN": "Zn",
    "CO": "Co",
    "PD": "Pd",
    "CR": "Cr",
    "FE": "Fe",
    "V": "V",
    "MN": "Mn",
    "HG": "Hg",
    "CD": "Cd",
    "YB": "Yb",
    "CA": "Ca",
    "SN": "Sn",
    "PB": "Pb",
    "EU": "Eu",
    "SR": "Sr",
    "SM": "Sm",
    "BA": "Ba",
    "RA": "Ra",
    "AL": "Al",
    "IN": "In",
    "Y": "Y",
    "LA": "La",
    "CE": "Ce",
    "PR": "Pr",
    "ND": "Nd",
    "GD": "Gd",
    "TB": "Tb",
    "DY": "Dy",
    "ER": "Er",
    "TM": "Tm",
    "LU": "Lu",
    "HF": "Hf",
    "ZR": "Zr",
    "U": "U",
    "PU": "Pu",
    "TH": "Th",
}
"""Contains mapping of metal types. Used to check if a residue atom name from a PDB is a metal."""