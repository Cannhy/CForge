"""
Public API of the four CForge tiers, organised by difficulty:

    - IntroductoryProblem  (introductory_load / introductory_load_not_fast)
    - EasyProblem          (easy_load         / easy_load_not_fast)
    - MediumProblem        (medium_load       / medium_load_not_fast)
    - HardProblem          (hard_load         / hard_load_not_fast)
"""

from evaluate.benchmarks.introductory import (
    IntroductoryProblem,
    load_code_generation_dataset as introductory_load,
    load_code_generation_dataset_not_fast as introductory_load_not_fast,
)

from evaluate.benchmarks.easy import (
    EasyProblem,
    load_code_generation_dataset as easy_load,
    load_code_generation_dataset_not_fast as easy_load_not_fast,
)

from evaluate.benchmarks.medium import (
    MediumProblem,
    load_code_generation_dataset as medium_load,
    load_code_generation_dataset_not_fast as medium_load_not_fast,
)

from evaluate.benchmarks.hard import (
    HardProblem,
    load_code_generation_dataset as hard_load,
    load_code_generation_dataset_not_fast as hard_load_not_fast,
)


__all__ = [
    "IntroductoryProblem", "introductory_load", "introductory_load_not_fast",
    "EasyProblem", "easy_load", "easy_load_not_fast",
    "MediumProblem", "medium_load", "medium_load_not_fast",
    "HardProblem", "hard_load", "hard_load_not_fast",
]
