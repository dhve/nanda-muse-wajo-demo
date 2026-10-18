"""Scene base class: beats, params, duration rules and lazy sprite building."""

from __future__ import annotations

from engine import brand


class Scene:
    name = ""
    nominal = 0.0          # default duration (slot length in the edit)
    beats: dict = {}       # name -> seconds from scene start
    params: dict = {}      # name -> default value
    background = "surface"
    min_hold = 0.5         # shortest settled hold allowed when compressing

    def __init__(self, duration=None, beats=None, params=None):
        p = {"lead": 0.0}
        p.update(self.params)
        for k, v in (params or {}).items():
            if k not in p:
                raise KeyError(f"unknown param {k!r} for {self.name}; known: {', '.join(p)}")
            p[k] = self._coerce(p[k], v)
        self.p = p
        b = dict(self.beats)
        for k, v in (beats or {}).items():
            if k not in b:
                raise KeyError(f"unknown beat {k!r} for {self.name}; known: {', '.join(b)}")
            b[k] = float(v)
        lead = float(p["lead"])
        self.b = {k: v + lead for k, v in b.items()}
        self.duration = float(duration) if duration else float(self.nominal) + lead
        self.configure()
        self._built = False

    @staticmethod
    def _coerce(default, value):
        if isinstance(value, str) and isinstance(default, bool):
            return value.lower() in ("1", "true", "yes", "on")
        if isinstance(default, int) and not isinstance(default, bool):
            return int(value)
        if isinstance(default, float):
            return float(value)
        return value

    # Hooks for subclasses.
    def configure(self) -> None:
        """Derive copy and timing from params and beats (cheap, no sprites)."""

    def build(self) -> None:
        """Make sprites (called once, lazily, in each process)."""

    def settle_time(self) -> float:
        """Time after which every frame is identical."""
        raise NotImplementedError

    def render(self, canvas, t: float) -> None:
        raise NotImplementedError

    def draw(self, canvas, t: float) -> None:
        if not self._built:
            self.build()
            self._built = True
        self.render(canvas, t)

    @classmethod
    def describe(cls) -> dict:
        s = cls()
        settle = s.settle_time()
        return {
            "nominal": cls.nominal,
            "min": round(settle + cls.min_hold, 3),
            "max": 60.0,
            "settle": round(settle, 3),
            "beats": dict(cls.beats),
            "params": {"lead": 0.0, **cls.params},
        }


def ease_move(t: float, start: float, dur: float) -> float:
    return brand.ease_in_out_cubic(brand.progress(t, start, dur))
