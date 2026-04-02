"""
test_fft_frequency.py -- FFT-дискриминаторы частоты (из Primer.m)
=================================================================

Тестирование дискриминаторных оценок частоты по FFT-спектру
комплексного сигнала. Воспроизводит MatLab-пример Primer.m
(fcalcdelay.m + discr3ea, discr3qa, discr2sd, discr2cg).

5 методов:
  exp  — 3-точечный, парабола на log|S|  (discr3ea.c)
  sqr  — 3-точечный, парабола на |S|     (discr3qa.c)
  lay  — 3-точечный, Jacobsen            (fcalcdelay.m)
  sd   — 2-точечный, суммарно-разностный (discrsd.c)
  cg   — 2-точечный, центр тяжести       (discrcg.c)

Запуск:
    python test_python/test_fft_frequency.py
"""
import sys
import numpy as np
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from PyCore.runner import TestRunner, SkipTest


# ═══════════════════════════════════════════════════════════════════ #
#  Реализации дискриминаторов (порт C-исходников + fcalcdelay.m)     #
# ═══════════════════════════════════════════════════════════════════ #

def create_signal(fsin, fd, N, a=1.0, an=1e-9):
    """Комплексная экспонента: s = a*exp(j*2pi*fsin*t) + noise."""
    t = np.arange(N) / fd
    sig = a * np.exp(1j * 2.0 * np.pi * fsin * t)
    if an > 0:
        sig += an / np.sqrt(2) * (np.random.randn(N) + 1j * np.random.randn(N))
    return sig


def compute_fft(signal, nfft, window="hamming"):
    """FFT с окном: fftshift(fft(signal * win, nfft))."""
    N = len(signal)
    win = np.hamming(N) if window == "hamming" else np.ones(N)
    return np.fft.fftshift(np.fft.fft(signal * win, nfft))


def make_freq_axis(nfft, fd):
    """Частотная ось после fftshift."""
    return np.fft.fftshift(np.fft.fftfreq(nfft, 1.0 / fd))


def _peak3(fft_data):
    """Индексы трёх бинов вокруг пика."""
    k = int(np.argmax(np.abs(fft_data)))
    N = len(fft_data)
    return (k - 1) % N, k, (k + 1) % N


def _top2(fft_data):
    """Индексы двух сильнейших бинов."""
    idx = np.argsort(np.abs(fft_data))
    return int(idx[-1]), int(idx[-2])


# --- LAY: Jacobsen (из fcalcdelay.m) ---
def fft_discr_lay(fft_data, f_axis):
    km, k, kp = _peak3(fft_data)
    Sm, S0, Sp = fft_data[km], fft_data[k], fft_data[kp]
    denom = 2.0 * S0 - Sm - Sp
    if abs(denom) > 1e-60:
        sigma = (Sp - Sm) / denom
        N = len(fft_data)
        fd = (f_axis[1] - f_axis[0]) * N
        return f_axis[k] - np.real(sigma) * fd / N
    return f_axis[k]


# --- EXP: discr3ea.c (парабола на log|S|) ---
def fft_discr_exp(fft_data, f_axis):
    km, k, kp = _peak3(fft_data)
    pts = sorted([
        (abs(fft_data[km]), f_axis[km]),
        (abs(fft_data[k]),  f_axis[k]),
        (abs(fft_data[kp]), f_axis[kp]),
    ], key=lambda p: p[1])
    a1, f1 = pts[0]; a2, f2 = pts[1]; a3, f3 = pts[2]
    eps = 1e-300
    if a1 < eps or a2 < eps or a3 < eps:
        return f_axis[k]
    z1, z2, z3 = np.log(a1), np.log(a2), np.log(a3)
    a_c = z1*(f2**2-f3**2) + z2*(f3**2-f1**2) + z3*(f1**2-f2**2)
    b_c = z1*(f2-f3) + z2*(f3-f1) + z3*(f1-f2)
    if abs(b_c) < 1e-300:
        return f_axis[k]
    xe = 0.5 * a_c / b_c
    span = f3 - f1
    xe = np.clip(xe, f1 - 0.5*span, f3 + 0.5*span)
    return xe


# --- SQR: discr3qa.c (парабола на |S|, формула Ao) ---
def fft_discr_sqr(fft_data, f_axis):
    km, k, kp = _peak3(fft_data)
    A1, A2, A3 = abs(fft_data[km]), abs(fft_data[k]), abs(fft_data[kp])
    x1, x2, x3 = f_axis[km], f_axis[k], f_axis[kp]
    eps = 1e-300
    if abs(A2 - A3) < eps:
        return x2 if abs(A2 - A1) < eps else (x1 if A1 > A2 else (x2+x3)/2)
    if abs(A2 - A1) < eps:
        return x3 if A3 > A2 else (x1+x2)/2
    Ao = (A2 - A1) / (A2 - A3)
    d = (Ao - 1)*x2 - Ao*x3 + x1
    if abs(d) < eps:
        return x2
    return 0.5 * ((Ao-1)*x2**2 - Ao*x3**2 + x1**2) / d


# --- SD: discrsd.c (2-точечный, мощность) ---
def fft_discr_sd(fft_data, f_axis, c=0.132497):
    k1, k2 = _top2(fft_data)
    A1 = abs(fft_data[k1])**2; A2 = abs(fft_data[k2])**2
    x1, x2 = f_axis[k1], f_axis[k2]
    s = A2 + A1
    if abs(s) < 1e-300:
        return (x1+x2)/2
    return (x1+x2)/2 + c * (A2-A1) / s


# --- CG: discrcg.c (2-точечный, амплитуда) ---
def fft_discr_cg(fft_data, f_axis):
    k1, k2 = _top2(fft_data)
    A1, A2 = abs(fft_data[k1]), abs(fft_data[k2])
    x1, x2 = f_axis[k1], f_axis[k2]
    s = A1 + A2
    if abs(s) < 1e-300:
        return (x1+x2)/2
    return (A1*x1 + A2*x2) / s


METHODS = {
    "exp": fft_discr_exp,
    "sqr": fft_discr_sqr,
    "lay": fft_discr_lay,
    "sd":  fft_discr_sd,
    "cg":  fft_discr_cg,
}


# ═══════════════════════════════════════════════════════════════════ #
#  Тесты                                                              #
# ═══════════════════════════════════════════════════════════════════ #

def _spectrum(fsin, fd=12e6, N=32):
    sig = create_signal(fsin, fd, N, an=0.0)
    return compute_fft(sig, N), make_freq_axis(N, fd)


class TestFFTBasic:
    """Базовые тесты FFT-дискриминаторов."""

    def test_exp_at_center(self):
        """EXP при fsin=0 -> f_est ~ 0."""
        spec, f = _spectrum(0.0)
        fe = fft_discr_exp(spec, f)
        assert abs(fe) < 100, f"EXP(0)={fe}"
        print(f"  [PASS] EXP at center: err={abs(fe):.1f} Hz")

    def test_sqr_at_center(self):
        spec, f = _spectrum(0.0)
        fe = fft_discr_sqr(spec, f)
        assert abs(fe) < 100, f"SQR(0)={fe}"
        print(f"  [PASS] SQR at center: err={abs(fe):.1f} Hz")

    def test_lay_at_center(self):
        spec, f = _spectrum(0.0)
        fe = fft_discr_lay(spec, f)
        assert abs(fe) < 100, f"LAY(0)={fe}"
        print(f"  [PASS] LAY at center: err={abs(fe):.1f} Hz")

    def test_exp_shifted(self):
        """EXP при delta=0.25 бина -> точная оценка."""
        fd, N = 12e6, 32
        fsin = fd / N / 4  # 93750 Hz
        spec, f = _spectrum(fsin, fd, N)
        fe = fft_discr_exp(spec, f)
        err = abs(fe - fsin)
        assert err < 10000, f"EXP err={err:.0f}"
        print(f"  [PASS] EXP shifted: f_est={fe:.0f}, err={err:.0f} Hz")


class TestFFTSweep:
    """Sweep-тест: ДХ (дискриминационная характеристика) по частоте."""

    def setUp(self):
        self.N, self.fd = 32, 12e6
        self.df = self.fd / self.N
        self.n_pts = 17
        self.fsin = np.linspace(-self.df/2, self.df/2, self.n_pts)

    def test_exp_monotonic(self):
        """EXP: оценка монотонно растёт при sweep."""
        self.setUp()
        ests = [fft_discr_exp(*_spectrum(fs, self.fd, self.N)) for fs in self.fsin]
        assert all(d > 0 for d in np.diff(ests)), "EXP not monotonic"
        print(f"  [PASS] EXP monotonic ({self.n_pts} pts)")

    def test_sqr_monotonic(self):
        self.setUp()
        ests = [fft_discr_sqr(*_spectrum(fs, self.fd, self.N)) for fs in self.fsin]
        assert all(d > 0 for d in np.diff(ests)), "SQR not monotonic"
        print(f"  [PASS] SQR monotonic ({self.n_pts} pts)")

    def test_exp_max_error(self):
        """EXP: макс ошибка < 10 кГц."""
        self.setUp()
        errs = [abs(fs - fft_discr_exp(*_spectrum(fs, self.fd, self.N)))
                for fs in self.fsin]
        mx = max(errs)
        assert mx < 10000, f"max err={mx:.0f}"
        print(f"  [PASS] EXP max error: {mx:.0f} Hz")

    def test_lay_correct_sign(self):
        """LAY: правильный знак оценки."""
        self.setUp()
        ok = 0
        for fs in self.fsin:
            if abs(fs) < self.df * 0.05:
                continue
            fe = fft_discr_lay(*_spectrum(fs, self.fd, self.N))
            assert (fs > 0 and fe > 0) or (fs < 0 and fe < 0), \
                f"sign: fsin={fs:.0f}, f_est={fe:.0f}"
            ok += 1
        print(f"  [PASS] LAY correct sign ({ok} pts)")


class TestFFTCompare:
    """Сравнение точности методов на FFT-спектре."""

    def test_exp_best(self):
        """EXP средняя ошибка < SQR < LAY."""
        fd, N = 12e6, 32; df = fd / N
        fsin_arr = np.linspace(-df/4, df/4, 21)
        errs = {m: [] for m in ["exp", "sqr", "lay"]}
        for fs in fsin_arr:
            spec, f = _spectrum(fs, fd, N)
            for m in errs:
                fe = METHODS[m](spec, f)
                errs[m].append(abs(fs - fe))
        me = {m: np.mean(e) for m, e in errs.items()}
        assert me["exp"] < me["sqr"], f"EXP({me['exp']:.0f}) >= SQR({me['sqr']:.0f})"
        assert me["exp"] < me["lay"], f"EXP({me['exp']:.0f}) >= LAY({me['lay']:.0f})"
        print(f"  [PASS] EXP({me['exp']:.0f}) < SQR({me['sqr']:.0f}) < LAY({me['lay']:.0f})")

    def test_accuracy_table(self):
        """Таблица точности всех 5 методов."""
        fd, N = 12e6, 32; df = fd / N
        fsin_arr = np.linspace(-df/4, df/4, 21)
        errs = {m: [] for m in METHODS}
        for fs in fsin_arr:
            spec, f = _spectrum(fs, fd, N)
            for m, func in METHODS.items():
                fe = func(spec, f)
                errs[m].append(abs(fs - fe))
        print("  Метод | Средняя     | Макс.")
        print("  ------+-------------+-----------")
        for m in ["exp", "sqr", "lay", "sd", "cg"]:
            print(f"  {m:5s} | {np.mean(errs[m]):9.0f} Hz | {np.max(errs[m]):7.0f} Hz")
        print("  [PASS] accuracy table printed")


# ═══════════════════════════════════════════════════════════════════ #

if __name__ == "__main__":
    runner = TestRunner()
    results = runner.run_all([
        TestFFTBasic(),
        TestFFTSweep(),
        TestFFTCompare(),
    ])
    runner.print_summary(results)
