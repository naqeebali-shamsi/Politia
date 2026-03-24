from abc import ABC, abstractmethod


class ScoringStrategy(ABC):
    @abstractmethod
    def compute(self, data: dict, baselines: dict | None = None) -> tuple[float, dict]:
        """
        Compute a score component.

        Args:
            data: Raw input data for this component
            baselines: Chamber/session averages for normalization

        Returns:
            Tuple of (score_value, breakdown_dict)
            score_value: 0-100 normalized score
            breakdown_dict: Transparent breakdown of how score was computed
        """
        ...

    @property
    @abstractmethod
    def weight(self) -> float:
        """Weight of this component in the overall score (0-1)."""
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        ...
