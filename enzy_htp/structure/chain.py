"""Definition for the Chain class. Chains primarily store Residue() objects and organize them
within the overall structure of an enzyme.

Author: Qianzhen (QZ) Shao <qianzhen.shao@vanderbilt.edu>
Author: Chris Jurich <chris.jurich@vanderbilt.edu>
Date: 2022-03-20
"""
from __future__ import annotations
from copy import deepcopy
from enzy_htp.core import _LOGGER
from typing import List
from enzy_htp.core.doubly_linked_tree import DoubleLinkNode

from enzy_htp.structure.atom import Atom

from .residue import Residue
#TODO(CJ): add a method for changing/accessing a specific residue

class Chain(DoubleLinkNode):
    """Class that represents a Chain of residues in a PDB file.

    Attributes:
        _name : The name of the chain as a string.
        _children/_residues : A list of Residue() objects or derived types.
        _parent/protein : the parent protein
    """

    def __init__(self, name: str, residues: List[Residue], parent=None):
        """Initiation of a Chain with a name and list of residues."""
        self._name = name
        self.set_parent(parent)
        self.set_children(residues)

        self._residues = self._children # alias
    #region === Getter-Attr (ref) ===
    @property
    def name(self) -> str:
        return self._name
    @name.setter
    def name(self, val):
        self._name = val

    @property
    def protein(self) -> str:
        return self.get_parent()
    @protein.setter
    def protein(self, val):
        self.set_parent(val)

    @property
    def residues(self) -> List[Residue]:
        """Access the child Residue() objects."""
        return self.get_children()
    @residues.setter
    def residues(self, val):
        self.set_children(val)

    def get_residue(self, traget_key: str) -> Residue:
        '''TODO: is there alt option for the key?'''
        pass

    @property
    def atoms(self) -> List[Atom]:
        '''get all children Atoms'''
        result = []
        for res in self:
            result.extend(res.atoms)
        return result
    #endregion

    # === Getter-Prop (cpy/new) ===
    def num_atoms(self) -> int:
        """Finds the total number of Atom() objects contained in the Residue() children objects."""
        total = 0
        for res in self.residues():
            total += res.num_atoms()
        return total

    def num_residues(self) -> int:
        """Returns number of Residue() or Residue()-dervied objects belonging to the Chain."""
        return len(self)

    # === Checker === 
    def is_peptide(self) -> bool:
        pass

    def is_metal(self) -> bool:
        """Checks if any metals are contained within the current chain."""
        return sum(list(map(lambda rr: rr.is_metal(), self._residues)))

    def is_HET(self) -> bool:
        for rr in self._residues:
            if not rr.is_canonical():
                return False
        return True #@shaoqz: why not use sum like above lol

    def is_empty(self) -> bool: #@shaoqz: @imp2 maybe name it is_empty?
        """Does the chain have any Residue()'s."""
        return len(self._residues) == 0

    def is_same_sequence(self, other: Chain) -> bool:
        """Comparison operator for use with other Chain() objects. Checks if residue list is identical in terms of residue name only."""
        self_residues: List[Residue] = self._residues
        other_residues: List[Residue] = other._residues
        # print(len(self_residues),'\t',len(other_residues))
        if len(self_residues) != len(other_residues):
            return False

        for s, o in zip(self_residues, other_residues):
            s: Residue
            o: Residue
            if not s.is_sequence_eq(o): #@shaoqz: this is a good idea of having different levels of comparsion @imp2 after reading this method I found here it already comparing residues in the same position we only need to compare the name but not the key
                return False
        return True

    def is_same_coord(self, other: Chain) -> bool:
        '''check if self is same as other in coordinate of every atom'''
        self_atoms = self.atoms
        self_atoms.sort(key=lambda a: a.num)
        self_coord = map(lambda x:x.coord, self_atoms)
        other_atoms = other.atoms
        other_atoms.sort(key=lambda a: a.num)
        other_coord = map(lambda x:x.coord, other_atoms)
        for s, o in zip(self_coord, other_coord):
            if s != o:
                return False
        return True    
        
    # === Editor ===
    def add_residue(self, new_res: Residue, sort_after: bool = True, overwrite: bool = False) -> None: #@shaoqz: @imp overwriting a residue is rarely a demand but instead inserting one with same name and index but different stru is.
        """Allows for insertion of a new Residue() object into the Chain. If the new Residue() is an exact # TODO work on overwriting
        copy, it fully overwrites the existing value. The sort_after flag specifies if the Residue()'s should
        be sorted by residue_number after the insertion.
        """
        for ridx, res in enumerate(self._residues):
            if new_res.name == res.name and new_res.num_ == res.num_: #@shaoqz: @imp should not work like this. Imaging the case where both residue is called LIG but they are different ligands. They are neither the same nor should be overwritten.
                self._residues[ridx] = deepcopy(new_res)
                break
        else:
            self._residues.append(new_res)

        self.rename(self._name) #@shaoqz: maybe better to change this residue attribute only?

        if sort_after:
            self._residues.sort(key=lambda r: r.idx()) #@shaoqz: @imp this does not work when two different residue have the same index which often happens when you want to add a ligand to the structure.

    def remove_residue(self, target_key: str) -> None: #@shaoqz: @imp2 target key should not require the name. We should minimize the prerequisite of any input since its for HTP.
        """Given a target_key str of the Residue() residue_key ( "chain_id.residue_name.residue_number" ) format,
        the Residue() is removed if it currently exists in the Chain() object."""
        for ridx, res in enumerate(self._residues):
            if res.residue_key == target_key:
                break
        else:
            return

        del self._residues[ridx] #@shaoqz: why not move this line inside the loop?
    
    def rename(self, new_name: str) -> None: #@shaoqz: using the 2-way link sheet will get rid of functions like this but both works.
        """Renames the chain and propagates the new chain name to all child Residue()'s."""
        self._name = new_name
        res: Residue
        for ridx, res in enumerate(self._residues):
            self._residues[ridx].set_chain(new_name) #@shaoqz: why not just use res?

    def renumber_atoms(self, start: int = 1) -> int: #@shaoqz: @imp need to record the mapping of the index  #@shaoqz: also need one for residues
        """Renumbers the Atom()'s inside the chain beginning with "start" value and returns index of the last atom.
        Exits if start index <= 0.
        """
        if start <= 0:
            _LOGGER.error(
                f"Illegal start number '{start}'. Value must be >= 0. Exiting..."
            )
            exit(1)
        self._residues = sorted(self._residues, key=lambda r: r.idx())
        idx = start
        num_residues: int = self.num_residues()
        for ridx, res in enumerate(self._residues):
            idx = self._residues[ridx].renumber_atoms(idx)
            idx += 1
            terminal = (ridx < (num_residues - 1)) and (
                res.is_canonical() and not self._residues[ridx + 1].is_canonical() #@shaoqz: @imp what does this mean? the TER line?
            )
            if terminal:
                idx += 1
        return idx - 1 

    # === Special ===
    def __getitem__(self, key: int) -> Residue:
        """Allows indexing into the child Residue() objects."""
        return self._residues[key]

    def __delitem__(self, key: int) -> None:
        """Allows deleting of the child Residue() objects."""
        del self._residues[key]

    def __len__(self) -> int:
        """Returns number of Residue() or Residue()-dervied objects belonging to the Chain."""
        return len(self._residues)

    #region === TODO/TOMOVE ===
    def get_pdb_lines(self) -> List[str]: #@shaoqz: @imp move to the IO class
        """Generates a list of PDB lines for the Atom() objects inside the Chain(). Last line is a TER."""
        result = list()
        num_residues: int = self.num_residues()
        for idx, res in enumerate(self._residues):
            terminal = (idx < (num_residues - 1)) and (
                res.is_canonical() and not self._residues[idx + 1].is_canonical()
            )
            result.extend(res.get_pdb_lines(terminal)) #@shaoqz: why terminal?
        result.append("TER")
        return result
    #endregion
