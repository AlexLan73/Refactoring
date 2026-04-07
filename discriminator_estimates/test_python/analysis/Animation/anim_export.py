"""
anim_export.py — Экспорт GIF анимаций (headless).

5 сценариев:
  S1: sweep_all          — sweep x0: -1.5 → +1.5
  S2: sweep_zoom_normal  — zoom на normal зону
  S3: noise_ramp         — нарастающий шум
  S4: step_change        — изменение шага сетки
  S5: auto_demo          — демо переключения AUTO EA↔E2

Запуск:
    cd discriminator_estimates/test_python
    python analysis/Animation/anim_export.py
"""

import sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path
from matplotlib.animation import FuncAnimation

# --- Пути ---
ANIM_DIR     = Path(__file__).resolve().parent
ANALYSIS_DIR = ANIM_DIR.parent
MODULE_DIR   = ANALYSIS_DIR.parent.parent
REPO_ROOT    = MODULE_DIR.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(ANALYSIS_DIR))
sys.path.insert(0, str(ANIM_DIR))

from anim_core import AnimScene
from PyCore.runner import TestRunner

OUT = MODULE_DIR / "Doc" / "plots" / "1_animation"
OUT.mkdir(parents=True, exist_ok=True)


def export(name, x0_fn, snr_fn, step_fn, n_frames=75, fps=8, dpi=100,
           xlim_override=None, dynamic_xlim=False, reset_rng=False,
           subtitle=None, smooth=0.0):
    """Универсальный экспортёр GIF.

    Args:
        name: имя файла (без .gif)
        x0_fn: f(frame) → x0
        snr_fn: f(frame) → snr
        step_fn: f(frame) → step
        n_frames: количество кадров
        fps: кадров в секунду
        dpi: разрешение
        xlim_override: (xmin, xmax) — переопределить xlim
        dynamic_xlim: включить динамический xlim (для S4)
        reset_rng: сбросить RNG перед экспортом
    """
    scene = AnimScene()
    scene.setup(figsize=(10, 7), mode='export')
    scene._dynamic_xlim = dynamic_xlim

    if xlim_override:
        scene.ax_main.set_xlim(xlim_override)

    if reset_rng:
        scene.rng = np.random.default_rng(seed=42)

    if smooth > 0:
        scene._smooth = smooth

    # Подпись сценария под основным заголовком
    if subtitle:
        scene.ax_main.set_title(
            scene.ax_main.get_title() + '\n' + subtitle,
            fontsize=10)

    def init():
        scene.update(x0_fn(0), snr_fn(0), step_fn(0))
        return scene.get_artists()

    def update(frame):
        return scene.update(x0_fn(frame), snr_fn(frame), step_fn(frame))

    anim = FuncAnimation(scene.fig, update, frames=n_frames,
                         init_func=init, blit=True, interval=1000 // fps)
    path = OUT / f"{name}.gif"
    anim.save(str(path), writer='pillow', fps=fps, dpi=dpi)
    plt.close(scene.fig)
    print(f"  [OK] {path.name} ({n_frames} frames, {fps} fps)")
    return path


# ══════════════════════════════════════════════════════════════════════ #
#  Тесты экспорта                                                       #
# ══════════════════════════════════════════════════════════════════════ #

def _verify_gif(path, min_frames=10):
    """Проверить что GIF валидный."""
    from PIL import Image
    assert path.exists(), f"GIF not created: {path}"
    im = Image.open(str(path))
    assert im.n_frames >= min_frames, f"Too few frames: {im.n_frames}"
    print(f"    → {path.name}: {im.n_frames} frames, {im.size}")


class TestExportGIF:
    """Тесты экспорта всех 5 GIF."""

    def test_s1_sweep_all(self):
        """S1: sweep x0 = -1.5 -> +1.5."""
        p = export("sweep_all",
                   x0_fn  = lambda f: -1.5 + 3.0 * f / 74,
                   snr_fn = lambda f: 0.0,
                   step_fn= lambda f: 1.0,
                   n_frames=75,
                   subtitle='\u041f\u0438\u043a \u0434\u0432\u0438\u0436\u0435\u0442\u0441\u044f '
                            '\u043e\u0442 \u22121.5 \u0434\u043e +1.5 \u2014 '
                            '\u0441\u0440\u0430\u0432\u043d\u0435\u043d\u0438\u0435 '
                            '\u0432\u0441\u0435\u0445 \u043c\u0435\u0442\u043e\u0434\u043e\u0432')
                   # Пик движется от -1.5 до +1.5 — сравнение всех методов
        _verify_gif(p)
        print("  [PASS] test_s1_sweep_all")

    def test_s2_sweep_zoom_normal(self):
        """S2: zoom normal zona, x0 = -0.5 -> +0.5."""
        p = export("sweep_zoom_normal",
                   x0_fn  = lambda f: -0.5 + 1.0 * f / 49,
                   snr_fn = lambda f: 0.0,
                   step_fn= lambda f: 1.0,
                   n_frames=50,
                   xlim_override=(-2, 2),
                   subtitle='\u041d\u043e\u0440\u043c\u0430\u043b\u044c\u043d\u0430\u044f '
                            '\u0437\u043e\u043d\u0430 (|x\u2080| \u2264 0.5) \u2014 '
                            '\u0432\u0441\u0435 \u043c\u0435\u0442\u043e\u0434\u044b '
                            '\u0442\u043e\u0447\u043d\u044b')
                   # Нормальная зона (|x₀| ≤ 0.5) — все методы точны
        _verify_gif(p)
        print("  [PASS] test_s2_sweep_zoom_normal")

    def test_s3_noise_ramp(self):
        """S3: shum rastyot, x0=0.2 fixirovan."""
        p = export("noise_ramp",
                   x0_fn  = lambda f: 0.2,
                   snr_fn = lambda f: 0.25 * f / 74,
                   step_fn= lambda f: 1.0,
                   n_frames=75,
                   reset_rng=True,
                   smooth=0.7,
                   subtitle='\u0428\u0443\u043c \u0440\u0430\u0441\u0442\u0451\u0442 '
                            '(SNR: 0 \u2192 0.25), '
                            '\u0441\u0433\u043b\u0430\u0436\u0438\u0432\u0430\u043d\u0438\u0435 EMA=0.7')
                   # Шум растёт (SNR: 0 → 0.25), сглаживание EMA=0.7
        _verify_gif(p)
        print("  [PASS] test_s3_noise_ramp")

    def test_s4_step_change(self):
        """S4: shag setki menyaetsya 0.3 -> 2.5."""
        p = export("step_change",
                   x0_fn  = lambda f: 0.2,
                   snr_fn = lambda f: 0.0,
                   step_fn= lambda f: 0.3 + 2.2 * f / 59,
                   n_frames=60,
                   dynamic_xlim=True,
                   subtitle='\u0428\u0430\u0433 \u0441\u0435\u0442\u043a\u0438 '
                            '\u0440\u0430\u0441\u0442\u0451\u0442 '
                            '(0.3 \u2192 2.5) \u2014 '
                            '\u0442\u043e\u0447\u043a\u0438 '
                            '\u0440\u0430\u0437\u044a\u0435\u0437\u0436\u0430\u044e\u0442\u0441\u044f')
                   # Шаг сетки растёт (0.3 → 2.5) — точки разъезжаются
        _verify_gif(p)
        print("  [PASS] test_s4_step_change")

    def test_s5_auto_demo(self):
        """S5: AUTO pereklyuchenie EA<->E2, x0 = -2.0 -> +2.0."""
        p = export("auto_demo",
                   x0_fn  = lambda f: -2.0 + 4.0 * f / 74,
                   snr_fn = lambda f: 0.0,
                   step_fn= lambda f: 1.0,
                   n_frames=75,
                   subtitle='\u0410\u0412\u0422\u041e: '
                            '\u042d\u0410 \u0432 \u0446\u0435\u043d\u0442\u0440\u0435, '
                            'E2-\u044d\u043a\u0441\u0442\u0440\u0430\u043f\u043e\u043b\u044f\u0446\u0438\u044f '
                            '\u043f\u043e \u043a\u0440\u0430\u044f\u043c '
                            '(|x\u2080| > 1)')
                   # АВТО: ЭА в центре, E2-экстраполяция по краям (|x₀| > 1)
        _verify_gif(p)
        print("  [PASS] test_s5_auto_demo")


if __name__ == "__main__":
    runner = TestRunner()
    results = runner.run(TestExportGIF())
    runner.print_summary(results)
