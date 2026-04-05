"""
anim_interactive.py — Интерактивное окно с слайдерами и кнопками.

Элементы управления:
  - Слайдер x0:   смещение пика (-1.5 … +1.5)
  - Слайдер SNR:  уровень шума (0.0 … 0.30)
  - Слайдер Step: шаг сетки (0.2 … 2.5)
  - Кнопка Play:  автоматический sweep x0
  - Кнопка Pause: остановка
  - Кнопка Rec:   запись GIF текущих настроек
  - Кнопка Reset: сброс на начальные значения

Запуск:
    cd discriminator_estimates/test_python
    python analysis/Animation/anim_interactive.py
"""

import sys
import numpy as np
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider, Button
from pathlib import Path

# --- Пути ---
ANIM_DIR     = Path(__file__).resolve().parent
ANALYSIS_DIR = ANIM_DIR.parent
MODULE_DIR   = ANALYSIS_DIR.parent.parent
REPO_ROOT    = MODULE_DIR.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(ANALYSIS_DIR))
sys.path.insert(0, str(ANIM_DIR))

from anim_core import AnimScene, INTERVAL_MS

OUT = ANIM_DIR / "output"
OUT.mkdir(parents=True, exist_ok=True)


def main():
    # --- Создание сцены ---
    scene = AnimScene()
    scene.setup(figsize=(14, 9), mode='interactive')
    fig = scene.fig

    # --- Слайдеры ---
    ax_sl_x0   = fig.add_axes([0.15, 0.18, 0.70, 0.02])
    ax_sl_snr  = fig.add_axes([0.15, 0.14, 0.70, 0.02])
    ax_sl_step = fig.add_axes([0.15, 0.10, 0.70, 0.02])

    slider_x0   = Slider(ax_sl_x0,   'x0',   -1.5, 1.5,  valinit=0.0,  valstep=0.01)
    slider_snr  = Slider(ax_sl_snr,  'SNR',   0.0,  0.30, valinit=0.0,  valstep=0.005)
    slider_step = Slider(ax_sl_step, 'Step',  0.2,  2.5,  valinit=1.0,  valstep=0.1)

    # --- Callback для слайдеров ---
    def on_slider_change(val):
        scene.update(slider_x0.val, slider_snr.val, slider_step.val)
        fig.canvas.draw_idle()

    slider_x0.on_changed(on_slider_change)
    slider_snr.on_changed(on_slider_change)
    slider_step.on_changed(on_slider_change)

    # --- Кнопки ---
    ax_btn_play  = fig.add_axes([0.15, 0.03, 0.12, 0.04])
    ax_btn_pause = fig.add_axes([0.30, 0.03, 0.12, 0.04])
    ax_btn_rec   = fig.add_axes([0.45, 0.03, 0.15, 0.04])
    ax_btn_reset = fig.add_axes([0.63, 0.03, 0.12, 0.04])

    btn_play  = Button(ax_btn_play,  '\u25b6 Play')
    btn_pause = Button(ax_btn_pause, '\u23f8 Pause')
    btn_rec   = Button(ax_btn_rec,   '\u23fa Rec GIF')
    btn_reset = Button(ax_btn_reset, '\u21ba Reset')

    # --- Play / Pause ---
    x0_play = [0.0]  # mutable container для nonlocal

    timer = fig.canvas.new_timer(interval=INTERVAL_MS)

    def play_step():
        x0_play[0] += 0.02
        if x0_play[0] > 1.5:
            x0_play[0] = -1.5
        slider_x0.set_val(round(x0_play[0], 2))

    timer.add_callback(play_step)

    def on_play(event):
        x0_play[0] = slider_x0.val
        timer.start()

    def on_pause(event):
        timer.stop()

    btn_play.on_clicked(on_play)
    btn_pause.on_clicked(on_pause)

    # --- Record GIF ---
    def on_record(event):
        timer.stop()
        print("Recording GIF...")
        scene.rng = np.random.default_rng(seed=42)
        frames = []
        from PIL import Image as PILImage
        for x0 in np.linspace(-1.5, 1.5, 75):
            scene.update(x0, slider_snr.val, slider_step.val)
            fig.canvas.draw()
            buf = fig.canvas.buffer_rgba()
            w, h = fig.canvas.get_width_height()
            img = PILImage.frombuffer('RGBA', (w, h), buf)
            frames.append(img.convert('RGB'))
        path = OUT / "recorded.gif"
        frames[0].save(str(path), save_all=True,
                       append_images=frames[1:],
                       duration=INTERVAL_MS, loop=0)
        print(f"Saved: {path}")
        # Восстановить текущую позицию
        scene.update(slider_x0.val, slider_snr.val, slider_step.val)
        fig.canvas.draw_idle()

    btn_rec.on_clicked(on_record)

    # --- Reset ---
    def on_reset(event):
        timer.stop()
        slider_x0.set_val(0.0)
        slider_snr.set_val(0.0)
        slider_step.set_val(1.0)

    btn_reset.on_clicked(on_reset)

    # --- Начальный update ---
    scene.update(0.0, 0.0, 1.0)
    plt.show()


if __name__ == "__main__":
    main()
