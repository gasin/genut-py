import logging
import os
import pickle
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class StateKey:
    filename: str
    funcname: str
    coverage: int


def is_simpler_obj(old: object, new: object) -> bool:
    """compare obj simplicity"""

    new_str = str(new)
    old_str = str(old)

    if len(old_str) < len(new_str):
        return False
    if len(new_str) < len(old_str):
        return True

    return new_str.count("0") > old_str.count("0")


class State:
    state: dict[StateKey, Any] = {}

    _is_loaded = False
    _is_saved = False

    CACHE_FILE = ".genut/cache.pkl"

    @classmethod
    def load(cls, use_cache: bool = False):
        if use_cache and not State._is_loaded and os.path.isfile(State.CACHE_FILE):
            State._is_loaded = True
            try:
                with open(State.CACHE_FILE, "rb") as f:
                    State.state = pickle.load(f)
                logger.info("cache is loaded")
            except AttributeError:
                logger.warning("failed to load cache")

    @classmethod
    def save(cls):
        if State._is_saved:
            return
        State._is_saved = True

        os.makedirs(".genut", exist_ok=True)
        with open(State.CACHE_FILE, "wb") as f:
            pickle.dump(State.state, f)

    @classmethod
    def update(cls, filename, funcname, coverage, callargs_pre, return_value, modified_args):
        key = StateKey(filename, funcname, coverage)
        if key not in State.state or is_simpler_obj(State.state[key][0], callargs_pre):
            State.state[key] = (callargs_pre, return_value, modified_args)

    @classmethod
    def get_items(cls, filename: str, funcname: str):
        return [
            value
            for key, value in State.state.items()
            if key.filename == filename and key.funcname == funcname
        ]
