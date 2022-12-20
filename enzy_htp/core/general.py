"""This module contains helper functions related to general python/python library features

Author: QZ Shao, <shaoqz@icloud.com>
Date: 2022-10-21
"""
from typing import List, Iterable, Tuple
import itertools

# == List related ==
def delete_base_on_id(target_list: list, target_id: int):
    """
    delete an element from a list base on its id() value
    """
    for i in range(len(target_list) - 1, -1, -1):
        if id(target_list[i]) == target_id:
            del target_list[i]

def get_interval_from_list(target_list: List[int]) -> Iterable[Tuple[int, int]]:
    """
    convert a list of int to the interval/range representation
    Returns:
        a generater of tuples with each indicating the start/end of the interval
    Example:
        >>> list(get_interval_from_list([1,2,3,6,7,8]))
        [(1,3),(6,8)]
    reference: https://stackoverflow.com/questions/4628333
    """
    # clean input
    target_list = sorted(set(target_list))
    # here use enum id as a ref sequence and group by the deviation
    for i, j in itertools.groupby(
            enumerate(target_list),
            lambda ref_vs_target: ref_vs_target[1] - ref_vs_target[0]):
        j = list(j)
        yield j[0][1], j[-1][1]
