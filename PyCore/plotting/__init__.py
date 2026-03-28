"""
plotting -- абстракции визуализации
====================================

Классы:
    IPlotter       -- абстрактный интерфейс (Strategy)
    PlotConfig     -- настройки стиля графиков
"""

from .plotter_base import IPlotter, PlotConfig

__all__ = ["IPlotter", "PlotConfig"]
