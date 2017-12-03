# Licensed under a 3-clause BSD style license - see LICENSE.rst
import os
from astropy.tests.helper import remote_data
from ...thermal import NEATM
from .. import track, stop, reset, to_text, to_bibtex


# get file path of a static data file for testing
def data_path(filename):
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    return os.path.join(data_dir, filename)


@remote_data
def test_text():
    track()
    neatm = NEATM()
    assert ['sbpy.thermal.NEATM:', 'method:', 'Harris', '1998,',
            '1998Icar..131..291H'] == to_text().split()
    reset()
    stop()


@remote_data
def test_bibtex():
    track()
    neatm = NEATM()
    with open(data_path('neatm.bib')) as bib_file:
        assert bibtex == bib_file.read()
    reset()
    stop()