"""This module defines StructureRegion 

Author: Chris Jurich <chris.jurich@vanderbilt.edu>
Author: Qianzhen (QZ) Shao, <shaoqz@icloud.com>
Date: 2023-12-30"""

from copy import deepcopy
import numpy as np

from typing import Callable, Dict, List, Tuple, Union

from ..structure import Structure, Atom
from ..residue import Residue, ResidueDummy
from .capping import (
    capping_with_residue_terminals,
    )
from ..structure_operation.charge import init_charge

from enzy_htp.core.logger import _LOGGER

class StructureRegion:
    """this class defines a region inside of Structure()
    by a list of Atom()s. The idea is similar to StruSelection
    (TODO think of merging them or make adaptor) but some Atom()
    could be capping atoms that does not exist in the original
    Structure().
    This class mainly serves as the abstract model of QM region or
    regions in multiscale QM/MM.
    It handles free valence capping during its creation using .capping
    submodule.
    It handles charge spin determination and atom index mapping. (i.e.: the index in
    self.atoms -> Atom(). This is used in aligning calc files that only contain this
    region.)
    It also handles changing the geometry within the same topology. (e.g.: in an 
    ensemble)
    Constructors:
        create_region_from_selection_pattern
        create_region_from_residue_keys

    Attributes:
        atoms
        
    Properties:
        TODO"""
    # TODO make a xyzinterface and support writing the region

    def __init__(self, atoms: List[Atom]):
        # attribute
        self.atoms_ = atoms
        # property
        self.atom_mapper_ = dict()
        for aa in self.atoms_: 
            self.atom_mapper_[aa.key] = aa

    @property
    def atoms(self) -> List[Atom]:
        """getter for atoms_"""
        return self.atoms_

    @atoms.setter
    def atoms(self, val: List[Atom]):
        """setter for atoms_"""
        self.atoms_ = val

    # region == prop getter ==
    @property
    def atom_mapper(self) -> Dict[str, Atom]:
        """getter for atom_mapper_"""
        return self.atom_mapper_

    def get_atom(self, key: str) -> Atom:
        """get atom using the key str following the get scheme
        from Structure()."""
        return self.atom_mapper_[key]

    def backbone_indices(self, index:int=0) -> List[int]:
        """get indices of backbone atoms in the region.
        Mostly used for indices-based atom freeze/constraint
        of QM packages. (e.g.: XTB)
        TODO: in which case we need index not 0 or 1?"""
        indices:List[int] = []
        for aidx,aa in enumerate(self.atoms):
            if aa.is_mainchain_atom():
                indices.append( aidx + index )
        return indices

    def get_atom_index_from_key(self, key: str, indexing:int=0) -> int:
        """get relative index of an atom in the region.
        Mostly used for indices-based atom freeze/constraint
        of QM packages. (e.g.: XTB)
        TODO: in which case we need index not 0 or 1?"""
        for aidx, aa in enumerate(self.atoms):
            if aa.key == key:
                return aidx + indexing
        else:
            _LOGGER.error(f"key: {key} not found in the region")
            raise ValueError

    def get_atom_index(self,
                       atom: Atom,
                       geom: Structure = None,
                       indexing:int=0) -> int:
        """get relative index of an atom in the region.
        Align the same atom object under a specific geometry"""
        result = None
        if geom is None:
            # same geometry
            for aidx, aa in enumerate(self.atoms):
                if aa is atom:
                    result = aidx + indexing
        else:
            # apply geometry first
            geom_atoms = self.atoms_from_geom(geom)
            for aidx, aa in enumerate(self.geom_atoms):
                if aa is atom:
                    result = aidx + indexing
        
        if result is None:
            _LOGGER.error(f"atom: {atom} not found in the region")
            raise ValueError
        
        return result

    def closest_heavy_atom(self, atom:Atom) -> Atom:
        """find the closest heavy atom to an atom within the region
        and from the same residue. TODO change name add capping."""
        distances = list()
        for aa in self.atoms:
            if aa.element == 'H' or aa.parent != atom.parent:
                distances.append(1000)
            else:
                distances.append( atom.distance_to(aa) )
        return self.atoms[np.argmin(distances)]

    def atoms_from_geom(self, geom: Structure) -> List[Atom]:
        """get the corresponding atoms from a specific geometry
        with the same topology
        Note: this design is because many operations in this
        class is only topology related. If create an obj for
        each geom (i.e.: Structure()), we will need to repeat
        those topology operations."""
        # topology check
        if self.is_same_topology(geom):
            pass
    
    @property
    def involved_residues(self) -> List[Residue]:
        """get all involved residues in the region"""
        result = set()
        for atom in self.atoms:
            res = atom.parent
            if not isinstance(res, ResidueDummy):
                result.add(res)
        return list(result)
        
    def involved_residues_with_free_terminal(self) -> Dict[str, List[Residue]]:
        """get all involved residue that have a terminal free valance
        i.e.: to determine whether the C-side or N-side terminal is in
        the region
        Returns:
            {
            "c_ter": [Residue, ...],
            "n_ter": [Residue, ...],            
            }
            
        Note that this does not consider already existing caps."""
        result = {
            "c_ter": [],
            "n_ter": [],
        }
        region_residues = self.involved_residues
        for res in region_residues:
            if res.is_canonical() or res.is_modified():
                c_side_res = res.c_side_residue()
                n_side_res = res.n_side_residue()
                if c_side_res is not None and c_side_res not in region_residues:
                    result["c_ter"].append(res)
                if n_side_res is not None and n_side_res not in region_residues:
                    result["n_ter"].append(res)
            else:
                _LOGGER.warning(f"{res._rtype} found. Not considered")
        return result

    def clone(self):
        """return a clone of self"""
        result = type(self).__new__(type(self))
        result.atoms = [at for at in self.atoms] # same atom but new list
        return result

    def get_net_charge(self) -> int:
        """get the net charge of the region"""
        # ncaa: user needs to define
        # caa: use a mapper from ff14SB)
        for res in self.involved_residues:
            pass
    
    def get_spin(self) -> int:
        """get the spin of the region"""
        pass
    # endregion

    # region == checker ==
    def has_atoms(self, atoms:List[Atom] ) -> bool:
        """determine whether the StructureRegion contain
        the given list of Atom()s"""
        for aa in atoms:
            if not self.has_atom( aa ):
                return False
        return True

    def has_atom(self, atom:Atom) -> bool:
        """determine whether the StructureRegion contain
        the given Atom()"""
        return atom in self.atoms_

    def is_same_topology(self, geom: Structure) -> bool:
        """determine if the geometry have the same topology with self"""
        self_top = self.atoms[0].root
        return self_top.is_same_topology(geom) # TODO add this in Structure

    def is_whole_residue_only(self) -> bool:
        """check whether self contain atoms that composes whole residues
        only"""
        # it means all involved residues has all its atoms in the region
        for res in self.involved_residues:
            if not self.has_atoms(res.atoms):
                return False
        return True
    # endregion

    def __getitem__(self, key:int) -> Atom:
        return self.atoms_[key]

def create_region_from_residue_keys(stru:Structure,
                            residue_keys:List[Tuple[str,int]],
                            capping_method: str = "res_ter_cap",
                            method_caps: Dict = None,
                            ) -> StructureRegion:
    """TODO(CJ)
    TODO align with the unified APIs."""

    res_atoms = []
    for res_key in residue_keys:
        res:Residue=stru.find_residue_with_key(res_key)
        res_atoms.extend(res.atoms)
    raw_region = StructureRegion(res_atoms)

    # capping
    if capping_method not in CAPPING_METHOD_MAPPER:
        _LOGGER.error(f"capping method ({capping_method}) not supported. Supported: {CAPPING_METHOD_MAPPER.keys()}")
        raise ValueError
    capping_func = CAPPING_METHOD_MAPPER[capping_method]
    capped_region = capping_func(raw_region, method_caps)

    return capped_region

def create_region_from_selection_pattern(
        stru: Structure,
        pattern: str,
        capping_method: str = "res_ter_cap",
        **kwargs,
    ) -> StructureRegion:
    """create StructureRegion from selection pattern.
    Args:
        stru:
            the structure that contains the target region
        pattern:
            the selection pattern in pymol style that defines the region
        capping_method:
            the keyword of the capping method.
            See CAPPING_METHOD_MAPPER for more info
        (method specific options)
        "res_ter_cap"
            nterm_cap: the name of the cap added to the N-ter
            cterm_cap: the name of the cap added to the C-ter
    Returns:
        the StructureRegion"""
    # TODO figure out the import design. We probably need to put pymol down?
    from ..structure_selection import select_stru
    # select
    stru_sele = select_stru(stru, pattern)
    raw_region = StructureRegion(atoms=stru_sele.atoms)

    # capping
    if capping_method not in CAPPING_METHOD_MAPPER:
        _LOGGER.error(f"capping method ({capping_method}) not supported. Supported: {CAPPING_METHOD_MAPPER.keys()}")
        raise ValueError
    capping_func = CAPPING_METHOD_MAPPER[capping_method]
    capped_region = capping_func(raw_region, **kwargs)

    return capped_region

CAPPING_METHOD_MAPPER: Dict[str, Callable[[StructureRegion], StructureRegion]] = {
    "res_ter_cap" : capping_with_residue_terminals,
    "residue_terminal_capping" : capping_with_residue_terminals,
}
