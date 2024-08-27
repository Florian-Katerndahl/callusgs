from typing import List
import pytest
import bibtexparser
from callusgs import utils


class TestUtils:
    def test_ogr2internal(self):
        raise RuntimeError

    @pytest.mark.parametrize(
        "months, output",
        [
            (["jan", "feb"], [1, 2]),
            (["feb", "jan"], [2, 1]),
            (
                [
                    "jan",
                    "feb",
                    "mar",
                    "apr",
                    "may",
                    "jun",
                    "jul",
                    "aug",
                    "sep",
                    "oct",
                    "nov",
                    "dec",
                ],
                [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
            ),
            (["all"], []),
        ],
    )
    def test_month_names_to_index(self, months: List[str], output: List[int]):
        assert utils.month_names_to_index(months) == output

    @pytest.mark.parametrize(
        "months", [["hello", "from", "the", "other", "side"], ["jan", "feb", ""]]
    )
    def test_wrong_months(self, months: List[str]):
        with pytest.raises(KeyError):
            utils.month_names_to_index(months)

    def test_empty_month_list(self):
        with pytest.raises(ValueError):
            utils.month_names_to_index([])

    @pytest.mark.parametrize(
        "product",
        [
            "landsat_em_c2_l1",
            "landsat_em_c2_l2",
            "landsat_etm_c2_l1",
            "landsat_etm_c2_l2",
            "landsat_ot_c2_l1",
            "landsat_ot_c2_l2",
            "landsat_ba_tile_c2",
            "landsat_dswe_tile_c2",
            "landsat_fsca_tile_c2",
        ],
    )
    def test_product_is_landsat(self, product: str):
        assert utils.product_is_landsat(product)

    @pytest.mark.parametrize("product", ["gmted2010"])
    def test_product_is_not_landsat(self, product: str):
        assert not utils.product_is_landsat(product)

    @pytest.mark.parametrize("product", ["gmted2010"])
    def test_product_is_dem(self, product: str):
        assert utils.product_is_dem(product)

    @pytest.mark.parametrize(
        "product",
        [
            "landsat_em_c2_l1",
            "landsat_em_c2_l2",
            "landsat_etm_c2_l1",
            "landsat_etm_c2_l2",
            "landsat_ot_c2_l1",
            "landsat_ot_c2_l2",
            "landsat_ba_tile_c2",
            "landsat_dswe_tile_c2",
            "landsat_fsca_tile_c2",
        ],
    )
    def test_product_is_not_dem(self, product: str):
        assert not utils.product_is_dem(product)

    @pytest.mark.parametrize(
        "doi",
        [
            "https://doi.org/10.5281/zenodo.13319174",
            "https://doi.org/10.5066/P9OGBGM6",
            "http://doi.org/10.5066/P9C7I13B",
            "https://doi.org/10.5066/P9IAXOVV",
        ],
    )
    def test_get_citation(self, doi: str):
        result = utils.get_citation(doi)
        assert bibtexparser.loads(result).entries
