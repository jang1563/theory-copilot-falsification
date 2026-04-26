"""Safe-ish equation evaluators shared by CLI and batch gate runners."""

from __future__ import annotations

import warnings

import numpy as np


_NUMPY_FUNCS = ("log", "log1p", "exp", "abs", "sqrt", "sin", "cos")


def make_equation_fn(equation_str: str, col_names: list[str]):
    """Build an evaluator for a gene-name equation against a feature matrix.

    Equations may reference biological column names (``TOP2A - EPAS1``) or
    legacy positional aliases (``x0 - x1``). Constant equations are broadcast to
    the sample dimension so downstream gate code always receives a score vector.
    """

    safe_globals = {"__builtins__": {}}
    np_ns = {k: getattr(np, k) for k in _NUMPY_FUNCS}

    def fn(X: np.ndarray) -> np.ndarray:
        ns = {col_names[i]: X[:, i] for i in range(len(col_names))}
        ns.update({f"x{i}": X[:, i] for i in range(X.shape[1])})
        ns.update(np_ns)
        with np.errstate(invalid="ignore", divide="ignore", over="ignore", under="ignore"):
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                result = eval(equation_str, safe_globals, ns)  # noqa: S307
        arr = np.asarray(result, dtype=float)
        if arr.ndim == 0:
            arr = np.full(X.shape[0], float(arr))
        elif arr.shape[0] != X.shape[0]:
            arr = np.broadcast_to(arr.ravel(), (X.shape[0],))
        return arr

    return fn
