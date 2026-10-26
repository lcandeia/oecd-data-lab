import pandas as pd
import pytest

from oecd_data_lab.refresh_2026 import merge_historical_data


def make(country, months, values, base='2015', source='COICOP_1999'):
    return pd.DataFrame({
        'country': [country] * len(months),
        'period': pd.to_datetime(months),
        'cpi_index': values,
        'source_dataset': [source] * len(months),
        'base_period': [base] * len(months),
        'observation_status': ['A'] * len(months),
    })


def test_append_2026_preserves_history():
    old = make('USA', ['2025-09-01', '2025-11-01'], [110., 111.])
    new = make('USA', ['2025-11-01', '2026-01-01'], [111., 113.])
    merged, revisions = merge_historical_data(old, new)
    assert len(merged) == 3
    assert '2025-10' not in merged.period.dt.strftime('%Y-%m').tolist()
    assert revisions.empty


def test_overlapping_revision_is_audited():
    old = make('BRA', ['2025-12-01'], [110.])
    new = make('BRA', ['2025-12-01', '2026-01-01'], [111., 112.])
    merged, revisions = merge_historical_data(old, new)
    assert len(revisions) == 1
    assert merged.iloc[0].cpi_index == pytest.approx(111.)


def test_rebase_is_rejected():
    old = make('BRA', ['2025-12-01'], [110.])
    new = make('BRA', ['2025-12-01', '2026-01-01'], [100., 101.], base='2025')
    with pytest.raises(ValueError, match='Ano-base|ano-base'):
        merge_historical_data(old, new)


def test_large_overlap_discrepancy_is_rejected():
    old = make('BRA', ['2025-12-01'], [110.])
    new = make('BRA', ['2025-12-01'], [90.])
    with pytest.raises(ValueError, match='5%'):
        merge_historical_data(old, new)
