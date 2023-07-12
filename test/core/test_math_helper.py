"""Testing enzy_hpt.core.math_helper.py
Author: Qianzhen (QZ) Shao <shaoqz@icloud.com>
Date: 2022-09-26
"""
import logging
import numpy as np
import enzy_htp
from enzy_htp.core import math_helper as mh


def test_check_valid_ph_good_input(caplog):
    """Testing that the check_valid_ph() function works for good input."""
    existing_level = enzy_htp._LOGGER.level
    enzy_htp._LOGGER.setLevel(logging.DEBUG)
    phValues = np.linspace(0, 14, 100)
    for ph in phValues:
        mh.check_valid_ph(ph)
        assert "assigned pH:" not in caplog.text

    enzy_htp._LOGGER.setLevel(existing_level)


def test_check_valid_ph_bad_input(caplog):
    """Testing that the check_valid_ph() functio fails for bad input."""
    existing_level = enzy_htp._LOGGER.level
    enzy_htp._LOGGER.setLevel(logging.DEBUG)
    mh.check_valid_ph(-1)
    assert "assigned pH: -1.00 out of range: [0.00,14.00]" in caplog.text
    mh.check_valid_ph(15)
    assert "assigned pH: 15.00 out of range: [0.00,14.00]" in caplog.text
    enzy_htp._LOGGER.setLevel(existing_level)

def test_get_geom_center():
    """test function works as expected"""
    test_list_of_p = [
        (1, 1, 1),
        (2, 2, 5)
    ]
    assert mh.get_geom_center(test_list_of_p) == (1.5, 1.5, 3)

def test_get_dihedral():
    """test if function works as expected"""
    test_points = [
        (33.49599838256836, 35.71099853515625, 26.554000854492188),
        (33.0880012512207, 37.07600021362305, 26.940000534057617),
        (34.00899887084961, 37.507999420166016, 28.075000762939453),
        (33.8380012512207, 38.87300109863281, 28.569000244140625),
    ]
    assert mh.get_dihedral(*test_points) == 176.48266861678636
