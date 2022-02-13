# EnzyHTP
  EnzyHTP is a holistic platform that allows high-throughput molecular simulation of enzymes. Molecular simulations, such as quantum mechanics (QM), molecular mechanics (MM), and QM/MM modeling, are highly applicable to the design and discovery of new biocatalysts. Molecular simulations provide time-resolved, atomic and electronic detail for enzymatic reactions, complementing experimental sequence and structure-level information. As such, expanding molecular simulation data can improve the predictive power of machine learning models to evaluate mutation effects in enzyme catalysis. However, large-scale collection of molecular simulation data presents a significant challenge due to complex demands. To build an enzyme model appropriate for simulations, multiple hierarchies of structural definitions and treatments must be established such as protein stoichiometry, binding site, predicting amino acid protonation state, addition of missing residues, performing an amino acid substitution, and creating reacting species. Most enzyme modeling practices use similar structural operations but rely on manual curation, which is highly inefficient and hampers reproducibility. EnzyHTP, a high-throughput enzyme simulation tool, bypasses these issues through automation of molecular model construction, mutation, sampling and energy calculation.
![](Four_modules_whitebg.png)

# Documentation
Currently we are still preparing documentations for EnzyHTP and the code itself is under refactoring. The document is expected to online along with the refactored code. 
For now, you can check our paper (https://pubs.acs.org/doi/10.1021/acs.jcim.1c01424) and corresponding use cases under /Test_file/FAcD_expanse

# Requirement
## External Program
- AmberTool/Amber
- Gaussian
- Multiwfn (for wavefunction analysis)
## Python Package
- python >= 3.6
- numpy
- pdb2pqr
- openbabel

# Installation 
## dependence
1. Install conda & create an environment
2. install numpy `conda install numpy`
3. Install openbabel `conda install openbabel -c conda-forge`
4. Install pdb2pqr 
```
git clone https://github.com/Electrostatics/pdb2pqr.git
cd pdb2pqr
pip install .
```
5. Install Multiwfn (install demo in author's blog: http://bbs.keinsci.com/thread-12020-1-1.html) (The LMO func seems not working for WSL) (Note that run Multiwfn on ACCRE requires loading the GCC module) 
