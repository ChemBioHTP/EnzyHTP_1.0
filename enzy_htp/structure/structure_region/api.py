"""This module defines StructureRegion 

Author: Chris Jurich <chris.jurich@vanderbilt.edu>
Author: Qianzhen (QZ) Shao, <shaoqz@icloud.com>
Date: 2023-12-30"""
from __future__ import annotations
from collections import defaultdict
from copy import deepcopy
import numpy as np
from typing import Callable, Dict, List, Tuple, Union

from ..structure import Structure, Atom
from ..residue import Residue
from ..noncanonical_base import NonCanonicalBase
from .capping import (
    capping_with_residue_terminals,
    ResidueCap,
    )

from enzy_htp.core.logger import _LOGGER
from enzy_htp.core.math_helper import round_by, is_integer

class StructureRegion:
    """this class defines a region inside of Structure()
    by a list of Atom()s. The idea is similar to StruSelection
    (TODO think of merging them or make adaptor) but some Atom()
    could be capping atoms that does not exist in the original
    Structure().
    This class mainly serves as the abstract model of QM region or
    regions in multiscale QM/MM. And note it is a topology level concept
    that is designed to combine with a set of geometries.
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
            for aidx, aa in enumerate(geom_atoms):
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
        Returns:
            a list of Atom()s in the same order
        Note: this design is because many operations in this
        class is only topology related. If create an obj for
        each geom (i.e.: Structure()), we will need to repeat
        those topology operations."""
        result = []

        # 1. topology check
        if not self.is_same_topology(geom):
            _LOGGER.error(f"geometry ({geom}) does not match region topology!")
            raise ValueError
        
        # 2. copy caps and align the based on linked residues
        geom_cap_mapper = {}
        for cap in self.caps:
            geom_cap_mapper[cap] = cap.apply_to_geom(geom)
        
        # 3. find corresponding atoms from geom
        for atom in self.atoms:
            # cap: find from geom caps
            if atom.parent.is_residue_cap():
                geom_cap = geom_cap_mapper[atom.parent]
                geom_atom = geom_cap.find_atom_name(atom.name)
                result.append(geom_atom)
            
            # non-cap: find from geom
            else:
                geom_res = geom.residue_mapper[atom.parent.key()]
                geom_atom = geom_res.find_atom_name(atom.name)
                result.append(geom_atom)

        return result
    
    @property
    def involved_residues(self) -> List[Residue]:
        """get all involved residues in the region"""
        result = set()
        for atom in self.atoms:
            res = atom.parent
            if not isinstance(res, ResidueCap):
                result.add(res)
        return list(result)

    @property
    def caps(self) -> List[ResidueCap]:
        """get all involved residue caps in the region"""
        result = set()
        for atom in self.atoms:
            res = atom.parent
            if isinstance(res, ResidueCap):
                result.add(res)
        return list(result)

    @property
    def atoms_by_residue(self) -> Dict[Residue, List[Atom]]:
        """group atoms in the region by containing residues."""
        result = defaultdict(list)
        for atom in self.atoms:
            result[atom.parent].append(atom)
        return result

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

    def clone_to_geometry(self, geom: Structure) -> StructureRegion:
        """return a clone of self that applys a specific geometry"""
        result = self.clone()
        result.atoms = self.atoms_from_geom(geom)
        return result

    def get_net_charge(self) -> int:
        """get the net charge of the region.
        Need to init_charge before using it. 
        
        This design is because external software are used for init_charge
        and thus it needs to be above _interface which can only called by
        the Science API layer."""
        net_charge = 0
        for res, atoms in self.atoms_by_residue.items():
            if res.is_noncanonical():
                res: NonCanonicalBase
                if self.has_whole_residue(res):
                    if res.net_charge is None:
                        _LOGGER.error(
                            f"NCAA ({res.name}) does not have charge."
                            " ALWAYS check and explicit assign it using"
                            " Structure.assign_ncaa_chargespin()")
                        raise ValueError
                    net_charge += res.net_charge
                    continue
    
            for atom in atoms:
                atom: Atom
                if not atom.has_init_charge():
                    _LOGGER.error(f" {atom} dont have charge. Please init_charge(stru_region) before using this function.")
                    raise ValueError
                net_charge += atom.charge
        if is_integer(net_charge, tolerance=0.01):
            net_charge = round_by(net_charge, 0.5)
        else:
            _LOGGER.error(f"getting a non-integer net_charge {net_charge}!")
            raise ValueError

        return net_charge
    
    def get_spin(self) -> int:
        """get the spin of the region"""
        spin = 1
        if not self.is_whole_residue_only():
            raise Exception("TODO. add support for init_spin")
        else:
            for res in self.involved_residues:
                if res.is_noncanonical():
                    res: NonCanonicalBase
                    if res.multiplicity is None:
                        _LOGGER.error(
                            f"NCAA ({res.name}) does not have spin."
                            " ALWAYS check and explicit assign it using"
                            " Structure.assign_ncaa_chargespin()")
                        raise ValueError
                    spin += res.multiplicity - 1 # m = 2S + 1 = 2S_0 + 2S' + 1 = m_0 + m' - 1
        return spin
    
    @property
    def topology(self) -> Structure:
        """get the correpsonding Structure() of self"""
        for atom in self.atoms:
            if not atom.parent.is_residue_cap():
                return atom.root()
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

    def has_whole_residue(self, res: Residue) -> bool:
        """whether self have every atoms in {res}"""
        return self.has_atoms(res.atoms)

    def is_same_topology(self, geom: Structure) -> bool:
        """determine if the geometry have the same topology with self"""
        return self.topology.is_same_topology(geom)

    def is_whole_residue_only(self) -> bool:
        """check whether self contain atoms that composes whole residues
        only"""
        for res in self.involved_residues:
            if not self.has_whole_residue(res):
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
    capping_func(raw_region, **kwargs)

    return raw_region

def create_region_from_full_stru(stru: Structure):
    """create StructureRegion of the full structure

    Returns:
        the StructureRegion"""
    return StructureRegion(
        atoms = stru.atoms
    )

CAPPING_METHOD_MAPPER: Dict[str, Callable[[StructureRegion], StructureRegion]] = {
    "res_ter_cap" : capping_with_residue_terminals,
    "residue_terminal_capping" : capping_with_residue_terminals,
}
