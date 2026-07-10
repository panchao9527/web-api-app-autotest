import pytest
from openpyxl import Workbook

from utils.data_loader import load_excel


def test_empty_excel_has_clear_error(tmp_path, monkeypatch):
    monkeypatch.setattr("utils.data_loader.DATA_DIR", tmp_path)
    workbook = Workbook()
    sheet = workbook.active
    sheet.delete_rows(1, sheet.max_row)
    workbook.save(tmp_path / "empty.xlsx")
    workbook.close()

    with pytest.raises(ValueError, match="没有表头"):
        load_excel("empty.xlsx")
