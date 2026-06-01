"""``textual`` — build a document × word contingency table from free text.

Ported from R FactoMineR 2.14 ``R/textual.r``. Tokenizes a free-text column,
counts word frequencies per document (or per level of a grouping factor), and
returns the contingency table plus a word-frequency summary. It does NOT run a
CA — the ``cont_table`` it produces feeds directly into :func:`factominer.CA` or
:func:`factominer.descfreq`.

The tokenizer mirrors R exactly: every separator character is mapped to ``;``
(R's positional ``chartr``), text is lowercased over ASCII ``A-Z`` only, runs of
``;`` collapse to one, a single leading ``;`` is stripped, and the result is
split on ``;``.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

# R's default ``sep.word`` (18 chars incl. a space and a newline). ``;`` is
# duplicated in R's string; harmless here.
_DEFAULT_SEP = "; (),?./:'!=+\n;{}-"
_AZ = str.maketrans("ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz")


@dataclass(frozen=True)
class TextualResult:
    """Result of :func:`textual`: the contingency table and the word summary."""

    cont_table: pd.DataFrame  # groups × words (integer counts)
    # Indexed by word (freq-descending order); column ``words`` holds the global
    # frequency and ``nb.list`` the number of documents containing the word
    # (matching R's — confusingly named — ``nb.words`` data frame).
    nb_words: pd.DataFrame


def _tokenize(text: str, sep_word: str, maj_in_min: bool) -> list[str]:
    """Replicate R's ``chartr`` → collapse → lead-strip → ``strsplit`` tokenizer."""
    s = "" if text is None or (isinstance(text, float) and np.isnan(text)) else str(text)
    s = s.translate(str.maketrans({c: ";" for c in sep_word}))
    if maj_in_min:
        s = s.translate(_AZ)  # lowercase ASCII A-Z only (R's chartr("A-Z","a-z"))
    while ";;" in s:
        s = s.replace(";;", ";")
    if s.startswith(";"):
        s = s[1:]
    return s.split(";")


def textual(
    tab: pd.DataFrame,
    num_text: int | str,
    contingence_by: int | str | list | None = None,
    maj_in_min: bool = True,
    sep_word: str | None = None,
) -> TextualResult:
    """Build a document × word contingency table from a free-text column.

    ``num_text`` selects the text column (by position or name). ``contingence_by``
    selects the grouping: ``None`` or the text column itself groups by document
    (row); a single column groups by that factor; a length-2 list crosses two
    factors (joined with ``.``). ``maj_in_min`` lowercases; ``sep_word`` overrides
    the separator set.
    """
    sep_word = _DEFAULT_SEP if sep_word is None else sep_word
    text_col = tab.columns[num_text] if isinstance(num_text, int) else num_text

    # Tokenize every document; build the global vocabulary (sorted unique tokens).
    docs = [_tokenize(t, sep_word, maj_in_min) for t in tab[text_col].tolist()]
    vocab = sorted({w for toks in docs for w in toks})

    # Per-document counts (documents × words).
    idx = {w: j for j, w in enumerate(vocab)}
    counts = np.zeros((len(docs), len(vocab)), dtype=np.int64)
    for i, toks in enumerate(docs):
        for w in toks:
            counts[i, idx[w]] += 1
    per_doc = pd.DataFrame(counts, index=list(tab.index), columns=vocab)

    # Group the documents.
    if contingence_by is None or _same_col(contingence_by, num_text, tab):
        grouped = per_doc  # one row per document
    else:
        keys = _group_keys(tab, contingence_by)
        grouped = per_doc.groupby(keys, sort=True).sum()
        grouped.index.name = None

    # nb.words: indexed by word, ordered as R's ``rev(order(global_freq))`` —
    # descending frequency, ties broken by descending vocabulary index
    # (reverse-alphabetical). Column ``words`` = the global frequency,
    # ``nb.list`` = the number of documents containing the word (R's naming).
    global_freq = per_doc.sum(axis=0).to_numpy()
    nb_list = (per_doc > 0).sum(axis=0).to_numpy()
    order = sorted(range(len(vocab)), key=lambda i: (int(global_freq[i]), i), reverse=True)
    nb_words = pd.DataFrame(
        {"words": [int(global_freq[i]) for i in order], "nb.list": [int(nb_list[i]) for i in order]},
        index=[vocab[i] for i in order],
    )
    return TextualResult(cont_table=grouped, nb_words=nb_words)


def _same_col(contingence_by, num_text, tab) -> bool:
    if isinstance(contingence_by, (list, tuple)):
        return False
    a = contingence_by if isinstance(contingence_by, str) else tab.columns[contingence_by]
    b = num_text if isinstance(num_text, str) else tab.columns[num_text]
    return a == b


def _group_keys(tab: pd.DataFrame, contingence_by) -> pd.Series:
    if isinstance(contingence_by, (list, tuple)):
        cols = [c if isinstance(c, str) else tab.columns[c] for c in contingence_by]
        return tab[cols].astype(str).agg(".".join, axis=1)
    col = contingence_by if isinstance(contingence_by, str) else tab.columns[contingence_by]
    return tab[col].astype(str)
