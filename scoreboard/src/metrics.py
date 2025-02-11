from abc import ABC, abstractmethod
from typing import Any, Optional

from opentelemetry import metrics


class Metrics(ABC):
    def __init__(self, name: str) -> None:
        self.name = name
        self.meter = metrics.get_meter(self.name)

        # score is common for all games
        self.score_gauge = self.meter.create_gauge(
            name=f"arcade.{self.name}.score",
            description=f"score for the game `{self.name}`",
        )

    @abstractmethod
    def process(self, game_data: dict[str, Any]) -> None:
        raise NotImplementedError()


class ImvadersMetrics(Metrics):
    _instance: Optional["ImvadersMetrics"] = None

    def __new__(cls) -> "ImvadersMetrics":
        if cls._instance is None:
            cls._instance = super().__new__(cls)

        return cls._instance

    def __init__(self) -> None:
        if hasattr(self, "initialized"):
            return

        super().__init__(name="imvaders")

        self.projectile_counter = self.meter.create_counter(
            name=f"arcade.{self.name}.projectiles",
            description=f"projectiles fired for the game `{self.name}`",
        )

        self.level_counter = self.meter.create_counter(
            name=f"arcade.{self.name}.level",
            description=f"level counter for the game `{self.name}`",
        )

        self.duration_counter = self.meter.create_counter(
            name=f"arcade.{self.name}.duration",
            description=f"duration of play time for the game `{self.name}`",
        )

        self.initialized = True

    def process(self, game_data: dict[str, Any]) -> None:
        attributes = {
            "title": self.name,
            "version": game_data.get("version", "unknown"),
            "player_name": game_data.get("player_name", "unknown"),
        }

        values = {
            "score": game_data.get("current_score", 0),
            "projectiles": game_data.get("projectiles", 0),
            "duration": game_data.get("duration", 0),
            "level": game_data.get("level", 0),
        }

        self.score_gauge.set(amount=values["score"], attributes=attributes)
        self.projectile_counter.add(amount=values["projectiles"], attributes=attributes)
        self.level_counter.add(amount=values["level"], attributes=attributes)
        self.duration_counter.add(amount=values["duration"], attributes=attributes)


class LoggerMetrics(Metrics):
    _instance: Optional["LoggerMetrics"] = None

    def __new__(cls) -> "LoggerMetrics":
        if cls._instance is None:
            cls._instance = super().__new__(cls)

        return cls._instance

    def __init__(self) -> None:
        if hasattr(self, "initialized"):
            return

        super().__init__(name="logger")

        self.initialized = True

    def process(self, game_data: dict[str, Any]) -> None:
        values = {
            "score": game_data.get("current_score", 0),
        }
        attributes = {
            "title": self.name,
            "version": game_data.get("version", "unknown"),
            "player_name": game_data.get("player_name", "unknown"),
        }

        self.score_gauge.set(amount=values["score"], attributes=attributes)


class BughuntMetrics(Metrics):
    _instance: Optional["BughuntMetrics"] = None

    def __new__(cls) -> "BughuntMetrics":
        if cls._instance is None:
            cls._instance = super().__new__(cls)

        return cls._instance

    def __init__(self) -> None:
        if hasattr(self, "initialized"):
            return

        super().__init__(name="bughunt")

        self.initialized = True

    def process(self, game_data: dict[str, Any]) -> None:
        values = {
            "score": game_data.get("current_score", 0),
        }
        attributes = {
            "title": self.name,
            "version": game_data.get("version", "unknown"),
            "player_name": game_data.get("player_name", "unknown"),
        }

        self.score_gauge.set(amount=values["score"], attributes=attributes)


def metric_factory(name: str) -> Metrics:
    if name == "imvaders":
        return ImvadersMetrics()
    elif name == "logger":
        return LoggerMetrics()
    elif name == "bughunt":
        return BughuntMetrics()

    raise Exception(f"unknown metric name: {name}")
