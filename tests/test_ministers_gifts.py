from __future__ import annotations

from datetime import date
from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import pytest
from pytest import MonkeyPatch
from ruamel.yaml import YAML

from ministers_gifts.download import URL, get_csv, store_parquet


def test_true_is_true():
    assert True is True


def test_mixed_dates_preserve_iso_and_uk_dates(monkeypatch: MonkeyPatch) -> None:
    source = pd.DataFrame({"Date": ["2026-06-10", "14/06/2026", "Nil Return"]})
    monkeypatch.setattr(pd, "read_csv", lambda *args, **kwargs: source.copy())

    result = get_csv(URL("https://example.com/Department__gifts.csv"))

    assert result["Date"].iloc[:2].tolist() == [date(2026, 6, 10), date(2026, 6, 14)]
    assert pd.isna(result["Date"].iloc[2])


def test_unchanged_parquet_preserves_bytes(tmp_path: Path) -> None:
    path = tmp_path / "gifts.parquet"
    source = pd.DataFrame({"Minister": ["Example", None], "Value": [1, 2]})
    source.to_parquet(path, compression=None)
    original = path.read_bytes()

    store_parquet(source, path)

    assert path.read_bytes() == original


def test_changed_parquet_retains_new_data(tmp_path: Path) -> None:
    path = tmp_path / "gifts.parquet"
    pd.DataFrame({"Value": [1]}).to_parquet(path)
    updated = pd.DataFrame({"Value": [2, 3]})

    store_parquet(updated, path)

    pd.testing.assert_frame_equal(pd.read_parquet(path), updated)


@pytest.mark.parametrize("resource", ["gifts", "hospitality"])
@pytest.mark.parametrize("version_path", ["", "versions/0.1.0"])
def test_date_schema_matches_stored_values(resource: str, version_path: str) -> None:
    package = (
        Path(__file__).resolve().parents[1]
        / "data/packages/ministers_gifts_and_hospitality"
        / version_path
    )
    metadata = YAML(typ="safe").load(package / f"{resource}.resource.yaml")
    date_field = next(
        field for field in metadata["schema"]["fields"] if field["name"] == "Date"
    )

    assert date_field["type"] == "date"
    assert pa.types.is_date(
        pq.read_schema(package / f"{resource}.parquet").field("Date").type
    )
