"""Scene registry. Each scene is a class with timing beats, params and a draw(canvas, t) method."""

from __future__ import annotations

from .base import Scene  # noqa: F401
from .intro import Intro
from .roles import Roles
from .step import Step
from .closing import Closing
from .endcard import Endcard

SCENES = {cls.name: cls for cls in (Intro, Roles, Step, Closing, Endcard)}


def build(name: str, duration=None, beats=None, params=None) -> Scene:
    if name not in SCENES:
        raise KeyError(f"unknown scene {name!r}; known: {', '.join(SCENES)}")
    return SCENES[name](duration, beats, params)
