"""Define functions for mutate Structure(). 
Science API:
    +mutate_stru()

Mutation is carried out by an underlying engine and the supported engines currently include:
    + Amber/tleap

Author: Qianzhen (QZ) Shao <shaoqz@icloud.com>
Date: 2022-10-24
"""

from typing import List
from enzy_htp.structure import Structure

def mutate_stru(stru: Structure,
                pattern: str, # because we need to support insertion or deletion
                engine: str = "tleap_min",
                in_place: bool=False) -> Structure:
    """
    This science API solves the problem of mutation assigning and protein structural
    prediction upon mutation.
    It means to determine which mutation to address and determine the structure of the
    mutant of the source protein caused by residue substitution, deletion, and insertion.
    (see also: structure_prediction module for an alternative solution)
    Args:
        stru: the target structure
        pattern: the pattern for describing a set of mutations to deploy
        engine: the engine (method) used for determine the mutated structure
            (current available keywords):
            tleap_min
            # TODO may need to add more arg when deletion and insertion are supported
        in_place: if change the structure in-place and return the reference
                  False means return a changed structure_obj and keep the original object
                  intact
                  (default is False since wild-type structure is expected to also available
                  in many applications)
    Raises:
        enzy_htp.core.exception.UnsupportedMethod if the supplied engine is not supported.
    Returns:
        the reference/copy of the changed structure (depends on the in_place value)

    *Pattern Syntax:*
        "section_1,section_2,section_3,..."
        The pattern is composed by sections seperate by comma and each section can be one of the
        format below:
        1. direct indication            : XA###Y
        2. random N mutation in a set   : r:N[mutation_set_patterns]
        3. all mutation in a set: a     : a:[mutation_set_patterns]

        The mutation_set_patterns is seperated by comma and each describes 2 things:
        1. position_pattern: a set of positions
                            (using the selection syntax in the selection module)
        2. target_aa_pattern: a set of target mutations apply to all positions in the current set
                            (using syntax in the target_aa_pattern module)
        The two pattern are seperated by ":" and a mutation_set_patterns looks like:
        "position_pattern_0:target_aa_pattern_0, ..."

        Overall an example of pattern will be:
        "RA154W, r:100[resi 289 around 4 and not resi 36:larger, proj(id 1000, id 2023, positive, 10):more_negative_charge]"
        * here proj() is a hypothetical selection function

    Details:
        The problem have two parts: 1. assigning the mutation 2. predict the mutant structure.
    Assigning the mutation
        (find more in XXX TODO: use real name)

    Predicting the mutant structure
        Unlike predicting the whole protein structure from sequence and smiles, mutating a
    structure from a reference structure involves only changes on a limit number of residues
    and perturbation of the rest of the structure (especially ligand binding, protonation state etc.)
    As a result, it can be solved using more efficient methods and predicting the whole structure
    from sketch. Note that the accuracy of the resulting structure varies base on the need. If followed
    by MD, the structure only needs to be good starting point of MD.
        There are 3 types of mutations in protein sequence: substitution, deletion, and insertion.
        Substitution is the most common type of the mutation. In this case, only the side-chain is
    replaced by another type of the side-chain. And determining the conformation of the new side-chain
    is the main challenge. It also relates to side-chain conformation prediction in the field of
    structural prediction.
        Deletion and insertion involve backbone changes.
    
    Avaible strageties for predicting mutated structure:
    Substitution:
        Direct replacement of the side-chain:
        - tleap_min (https://pubs.acs.org/doi/full/10.1021/acs.jcim.1c01424)
            The most simple way to get a mutant structure. It 1. place the new side-chain using a
            constant conformation (relative to backbone) and 2. relax the crude mutant structure using
            MM minimization.

            Consider limited change of other side chains in MM minimization
            Not consider backbone change

            * This method particularly has problem when mutating a small residue to a larger one. In this
            case, collision may appears in the mutated structure and the MM minimization is responsible
            for resolving it. But in extreme cases, there are unresolvable collision such as the carbon
            chain is trapped in a phenyl ring. And currently we don't have a method to detect such trapping.
            The method is only used as a place holder for 1st version EnzyHTP. We have encounter any problem
            brought by the accuracy of the mutation when using this method in workflows but users should be
            cautious with it and consider it a potential source of absured results.
        
        Side-chain rotamer library:
        (most used in the field)
        - SCWRL4 (http://dunbrack.fccc.edu/lab/scwrl)
            Not consider other side-chain change
            Not consider backbone change
        - PyMol (https://github.com/schrodinger/pymol-open-source)
            Not consider other side-chain change
            Not consider backbone change
        - Phyre2
            Consider other side-chain change
            Not consider backbone change
            * seems having a derived pipeline Missense3D addressing the challenge (https://www.sciencedirect.com/science/article/pii/S0022283619302037?via%3Dihub#s0050)
            * related discussion in its website (http://www.sbg.bio.ic.ac.uk/phyre2/html/help.cgi?id=help/faq)
        
        Machine learning methods:
        - Packpred (http://cospi.iiserpune.ac.in/packpred/, https://www.frontiersin.org/articles/10.3389/fmolb.2021.646288/full, https://github.com/kuanpern/PackPred)
          * find a summary of the missence mutation in the intro of the paper
            Unknown
        
        MCMC search globally in side-chains:
        - Modeller
            Fully consider other side-chain change
            Not consider backbone change
        - SWISSMODEL
            Fully consider other side-chain change
            Not consider backbone change
    
    Insertion/Deletion:
        - Phyre4
            see http://www.sbg.bio.ic.ac.uk/phyre2/html/help.cgi?id=help/faq
            works mainly <5 AA change
    """

    # assign mutation (where to mutant to what)
    # (pattern, stru) -> (MutaFlag)
    mutation_flags = assign_mutation(stru, pattern)

    # deploy mutation (determine mutant structure)
    # stru -> stru

def assign_mutation(stru: Structure, pattern: str) -> List[str]:
    """
    decode the user assigned {pattern} based on the {stru} and get a list of mutation flags
    that direct indicate the mutation
    Args:
        stru: the target structure
        pattern: the pattern that defines the mutation
    Return:
        a list of mutation_flag in the form of XA###Y. Where X and Y is the residue before and
    after mutation, A### is the chain id and the residue index.
    """
    # decode the pattern
    # write a new module about mutation pattern?

