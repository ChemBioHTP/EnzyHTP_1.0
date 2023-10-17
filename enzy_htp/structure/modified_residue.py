"""Specialization of the Residue() class for a Modified Residues. 
In addition to Residue() object, has net_charge etc. attributes.
Meant to be stored alongside other Residue() and Residue() derived objets (MetalUnit() and Solvent()) inside of the
Chain() object.

Author: Qianzhen (QZ) Shao <shaoqz@icloud.com>
Date: 2023-10-12
"""
from __future__ import annotations

from copy import deepcopy

from .atom import Atom
from typing import List
from .residue import Residue
import enzy_htp.chemical as chem
from enzy_htp.core import _LOGGER


class ModifiedResidue(Residue):
    """Represents a specific ModifiedResidue found in a .pdb file. (#@shaoqz: a non-covalently binding small molecule to the protein part of the enzyme. decouple with PDB)
        Typically created from a base Residue() object using
        the residue_to_modified_residue() method found in enzy_htp.structure.modified_residue.py. In addition to base attributes, has
        net_charge attribute which is Union[float,None]. The value is_modified_residue() has been hard-coded to True and
        ModifiedResidue.rtype_ is set to ResidueType.NONCANONICAL. Meant to be stored alongside other Residue() and Residue()-derived
        classes (MetalUnit() and Solvent()) in Chain() objects.

    Attributes:
        net_charge : The net charge of the molecule as an int.
    """

    def __init__(self, residue_idx: int, residue_name: str, atoms: List[Atom], parent=None, **kwargs):
        """
        Constructor for ModifiedResidue. Identical to Residue() ctor but also takes net_charge value.
        """
        self.net_charge = kwargs.get("net_charge", None)
        self._multiplicity = kwargs.get("multiplicity", None)
        Residue.__init__(self, residue_idx, residue_name, atoms, parent)
        self.rtype = chem.ResidueType.NONCANONICAL

    # === Getter-Attr ===
    @property
    def net_charge(self) -> int:
        """Getter for the net_charge attribute."""
        return self._net_charge

    @net_charge.setter
    def net_charge(self, val: int):
        """Setter for the net_charge attribute."""
        self._net_charge = val

    @property
    def multiplicity(self) -> int:
        """Getter for the multiplicity attribute."""
        return self._multiplicity

    @multiplicity.setter
    def multiplicity(self, val: int):
        """Setter for the multiplicity attribute."""
        self._multiplicity = val

    # === Getter-Prop ===
    def clone(self) -> ModifiedResidue:
        """Creates deecopy of self."""
        return deepcopy(self)

    # === Checker ===
    def is_modified_residue(self) -> bool:
        """Checks if the Residue is a modified_residue. Always returns True for this specialization."""
        return True

    # === Editor ===
    def fix_atom_names(self) -> None:
        """
        Atom names should be unique in a modified_residue.
        This method assign atoms with valid names.
        """
        name_list = self.atom_name_list
        new_name_list = chem.get_valid_generic_atom_name(name_list)
        for name, atom in zip(new_name_list, self.atoms):
            if atom.name != name:
                _LOGGER.info(f"found atom with invalid name {atom}. changing it to {name}")
                atom.name = name

    # === Special ===
    def __str__(self) -> str:
        return f"ModifiedResidue({self._idx}, {self._name}, atom:{len(self._atoms)}, {self._parent})"


def residue_to_modified_residue(residue: Residue, net_charge: float = None) -> ModifiedResidue:
    """Convenience function that converts Residue to modified_residue."""
    return ModifiedResidue(residue.idx, residue.name, residue.atoms, residue.parent, net_charge=net_charge)
