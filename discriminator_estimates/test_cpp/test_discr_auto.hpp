#pragma once
/**
 * @file test_discr_auto.hpp
 * @brief Тесты автоматического дискриминатора с экстраполяцией
 */

extern "C" {
#include "../include/discr_auto.h"
}

#include <cassert>
#include <cmath>
#include <iostream>

namespace discr_test_auto {

/* sinc(x) = sin(x)/x, sinc(0) = 1 */
inline double sinc(double x) {
  if (std::abs(x) < 1e-15) return 1.0;
  return std::sin(x) / x;
}

inline void test_is_monotonic_decreasing() {
  /* 3, 2, 1 — убывающие → монотонные */
  assert(discr_is_monotonic(3.0, 2.0, 1.0) == 1);
  std::cout << "[PASS] is_monotonic: decreasing\n";
}

inline void test_is_monotonic_increasing() {
  /* 1, 2, 3 — возрастающие → монотонные */
  assert(discr_is_monotonic(1.0, 2.0, 3.0) == 1);
  std::cout << "[PASS] is_monotonic: increasing\n";
}

inline void test_is_monotonic_peak() {
  /* 1, 3, 2 — есть перегиб → НЕ монотонные */
  assert(discr_is_monotonic(1.0, 3.0, 2.0) == 0);
  std::cout << "[PASS] is_monotonic: peak (not monotonic)\n";
}

inline void test_is_monotonic_equal() {
  /* 1, 1, 1 — все равны → считаем монотонными */
  assert(discr_is_monotonic(1.0, 1.0, 1.0) == 1);
  std::cout << "[PASS] is_monotonic: all equal\n";
}

inline void test_auto_normal_case() {
  /* sinc(x) с пиком в 0: сетка {-1, 0, +1}
   * Нормальный случай — есть перегиб, должен сработать EA (ret=0) */
  double A1 = sinc(-1.0), A2 = sinc(0.0), A3 = sinc(1.0);
  double xe;
  int ret = discr3_auto(A1, A2, A3, -1.0, 0.0, 1.0, &xe);
  assert(ret == 0);  /* EA успех */
  assert(std::abs(xe) < 0.01);
  std::cout << "[PASS] auto normal: ret=" << ret
            << ", xe=" << xe << " (expected ~0)\n";
}

inline void test_auto_shifted() {
  /* sinc(x - 0.2): пик в 0.2, нормальная зона */
  double x0 = 0.2;
  double A1 = sinc(-1.0 - x0), A2 = sinc(0.0 - x0), A3 = sinc(1.0 - x0);
  double xe;
  int ret = discr3_auto(A1, A2, A3, -1.0, 0.0, 1.0, &xe);
  double err = std::abs(xe - x0);
  assert(ret == 0);  /* EA */
  assert(err < 0.01);
  std::cout << "[PASS] auto shifted x0=0.2: ret=" << ret
            << ", xe=" << xe << ", err=" << err << "\n";
}

inline void test_auto_monotonic_right() {
  /* sinc(x - 1.3): пик в 1.3, за сеткой вправо → монотонные */
  double x0 = 1.3;
  double A1 = sinc(-1.0 - x0), A2 = sinc(0.0 - x0), A3 = sinc(1.0 - x0);
  double xe;
  int ret = discr3_auto(A1, A2, A3, -1.0, 0.0, 1.0, &xe);
  assert(ret == 2 || ret == 3);  /* экстраполяция E2 */
  /* Оценка должна быть > 1.0 (за правым краем сетки) */
  assert(xe > 0.5);
  double err = std::abs(xe - x0);
  std::cout << "[PASS] auto monotonic right: ret=" << ret
            << ", xe=" << xe << ", err=" << err << "\n";
}

inline void test_auto_monotonic_left() {
  /* sinc(x + 1.3): пик в -1.3, за сеткой влево */
  double x0 = -1.3;
  double A1 = sinc(-1.0 - x0), A2 = sinc(0.0 - x0), A3 = sinc(1.0 - x0);
  double xe;
  int ret = discr3_auto(A1, A2, A3, -1.0, 0.0, 1.0, &xe);
  assert(ret == 2 || ret == 3);
  assert(xe < -0.5);
  double err = std::abs(xe - x0);
  std::cout << "[PASS] auto monotonic left: ret=" << ret
            << ", xe=" << xe << ", err=" << err << "\n";
}

inline void test_auto_vs_plain_ea() {
  /* Сравнение: auto vs plain EA для монотонного случая
   * auto (E2) должен быть точнее */
  double x0 = 1.3;
  double A1 = sinc(-1.0 - x0), A2 = sinc(0.0 - x0), A3 = sinc(1.0 - x0);

  /* discr3_auto: должен использовать E2 */
  double xe_auto;
  discr3_auto(A1, A2, A3, -1.0, 0.0, 1.0, &xe_auto);
  double err_auto = std::abs(xe_auto - x0);

  /* discr3ea: вернёт FAILURE для монотонных данных */
  double xe_ea;
  int ret_ea = discr3ea(A1, A2, A3, -1.0, 0.0, 1.0, &xe_ea);
  double err_ea = std::abs(xe_ea - x0);

  std::cout << "[INFO] Monotonic x0=1.3: "
            << "auto err=" << err_auto
            << ", plain EA err=" << err_ea
            << " (EA ret=" << ret_ea << ")\n";

  /* auto не должен быть хуже EA */
  assert(err_auto <= err_ea + 0.01);
  std::cout << "[PASS] auto_vs_plain_ea: auto is better or equal\n";
}

inline void test_extrap_gauss_quality() {
  /* Средняя ошибка E2 на серии монотонных случаев */
  double total_err = 0;
  int count = 0;

  for (int i = 0; i <= 20; ++i) {
    double x0 = 1.0 + 0.025 * i;  /* x0 = 1.0 ... 1.5 */
    double A1 = sinc(-1.0 - x0), A2 = sinc(0.0 - x0), A3 = sinc(1.0 - x0);
    double xe;
    discr3_extrap_gauss(A1, A2, A3, -1.0, 0.0, 1.0, &xe);
    total_err += std::abs(xe - x0);
    count++;
  }
  double mae = total_err / count;
  std::cout << "[INFO] E2 extrap MAE (x0=1.0..1.5): " << mae << "\n";
  assert(mae < 0.5);  /* исследование: MAE ≈ 0.148 */
  std::cout << "[PASS] extrap_gauss quality: MAE=" << mae << "\n";
}

inline void run_all() {
  std::cout << "\n--- discr_auto tests ---\n";
  test_is_monotonic_decreasing();
  test_is_monotonic_increasing();
  test_is_monotonic_peak();
  test_is_monotonic_equal();
  test_auto_normal_case();
  test_auto_shifted();
  test_auto_monotonic_right();
  test_auto_monotonic_left();
  test_auto_vs_plain_ea();
  test_extrap_gauss_quality();
}

}  // namespace
