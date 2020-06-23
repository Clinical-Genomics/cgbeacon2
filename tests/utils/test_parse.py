# -*- coding: utf-8 -*-
import pybedtools
from cgbeacon2.resources import panel1_path, panel2_path
from cgbeacon2.utils.parse import (
    merge_intervals,
    extract_variants,
    bnd_mate_name,
    sv_end,
)

ALT = "G]17:198982]"


def test_bnd_mate_name():
    """Test the function that extract mate name from a variant ALT field"""

    mate = bnd_mate_name(ALT, "2")
    assert mate == "17"


def test_sv_end_SVEND():
    """Test the function that calculates the end coordinate of a structural variant in the presence of SVEND.

    Example:
    2 321682 . T <DEL> 6 PASS SVTYPE=DEL;END=321887;SVLEN=-205;CIPOS=-56,20;CIEND=-10,62 GT:GQ 0/1:12

    """
    end = sv_end(pos=321682, alt="<DEL>", svend=321887, svlen=-205)
    assert end == 321886


def test_sv_end_BND():
    """Test the function that calculates the end coordinate of a BND structural variant.

    Example:
    2	321681	bnd_W	G	G]17:198982]	6	PASS	SVTYPE=BND;MATEID=bnd_Y	GT	0/1
    """
    end = sv_end(pos=321681, alt=ALT, svend=None, svlen=None)
    assert end == 198981


def test_merge_intervals():
    """Test function using pyBedTools for merging intervals from one or more panels"""

    a = pybedtools.example_bedtool("a.bed")  # path to test file a
    """ This file looks like this:
    chr1	1	100	feature1	0	+
    chr1	100	200	feature2	0	+
    chr1	150	500	feature3	0	-
    chr1    900	950	feature4	0	+
    """
    assert len(a) == 4

    b = pybedtools.example_bedtool("b.bed")  # path to test file b
    """ This file looks like this:
    chr1	155	200	feature5	0	-
    chr1	800	901	feature6	0	+
    """
    assert len(b) == 2

    merged_bed = merge_intervals([a, b])
    assert len(merged_bed) == 2
    """Merged file looks like this:
    chr1	1	500
    chr1	800	950
    """


def test_merge_demo_intervals():
    """Test function using pyBedTools for merging intervals from one or more panels using demo intervals"""

    a = pybedtools.BedTool(panel1_path)
    assert len(a) == 4
    b = pybedtools.BedTool(panel2_path)
    assert len(b) == 3

    merged_bed = merge_intervals([a, b])
    assert len(merged_bed) == len(a) + len(b) - 1  # a and b have a shared interval


def test_extract_variants_no_vcf_file():
    """When VCF file is not a valid file then the extract variants functions returns None"""

    results = extract_variants("wrong_VCF_path")
    assert results is None
