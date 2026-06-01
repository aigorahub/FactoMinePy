"""Parity tests for ``textual`` (document × word contingency table) vs R.

Deterministic integer counting → exact match. Checks the ``cont_table`` (by
group × word label) and the ``nb_words`` summary (the word list in R's
frequency-descending / reverse-alphabetical-tie order, plus ``nb.list``).
"""

from __future__ import annotations

import pandas as pd

from factominer import textual
from factominer.datasets import load_textual_synth


def _cont(records) -> pd.DataFrame:
    df = pd.DataFrame(records)
    return df.set_index([c for c in df.columns if str(c) == "_row"][0])


def _check_cont_table(py: pd.DataFrame, r_records):
    r = _cont(r_records)
    assert set(py.index.astype(str)) == set(r.index.astype(str)), "group set"
    assert set(py.columns) == set(r.columns), f"word set: py={set(py.columns)} r={set(r.columns)}"
    for g in r.index:
        for w in r.columns:
            assert int(py.loc[g, w]) == int(r.loc[g, w]), f"count [{g}, {w}]"


def _check_nb_words(py: pd.DataFrame, r_records):
    # R's nb.words: row name = word, column "words" = global frequency,
    # "nb.list" = #documents. Same word order (freq-desc, reverse-alpha ties).
    r = pd.DataFrame(r_records).set_index([c for c in pd.DataFrame(r_records).columns if str(c) == "_row"][0])
    assert list(py.index) == list(r.index), f"nb_words order: py={list(py.index)} r={list(r.index)}"
    assert [int(v) for v in py["words"]] == [int(v) for v in r["words"]], "nb_words frequency"
    assert [int(v) for v in py["nb.list"]] == [int(v) for v in r["nb.list"]], "nb.list"


def test_textual_by_group(r_textual_synth_grp):
    res = textual(load_textual_synth(), num_text="review", contingence_by="grp")
    _check_cont_table(res.cont_table, r_textual_synth_grp["cont_table"])
    _check_nb_words(res.nb_words, r_textual_synth_grp["nb_words"])


def test_textual_by_document(r_textual_synth_doc):
    res = textual(load_textual_synth(), num_text="review", contingence_by="review")
    _check_cont_table(res.cont_table, r_textual_synth_doc["cont_table"])
    _check_nb_words(res.nb_words, r_textual_synth_doc["nb_words"])
