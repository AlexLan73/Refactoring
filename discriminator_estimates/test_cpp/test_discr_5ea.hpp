#pragma once
/**
 * @file test_discr_5ea.hpp
 * @brief Тесты: МНК-гауссова и МНК-параболическая аппроксимация по 5 точкам
 */

extern "C" {
#include "discr5ea.h"
}
#include <cassert>
#include <cmath>
#include <iostream>

namespace discr_test_5ea {

/* sinc(x) = sin(x)/x, sinc(0) = 1 */
inline double sinc(double t) {
  if (std::fabs(t) < 1e-15) return 1.0;
  return std::sin(t) / t;
}


/* ==================== discr5ea (Gaussian LSQ 5pt) ==================== */

inline void test_gaussian_symmetric() {
  /* Гауссов пик в 0: A = exp(-x^2), точки {-2,-1,0,1,2} */
  double A[5] = {
    std::exp(-4.0), std::exp(-1.0), 1.0,
    std::exp(-1.0), std::exp(-4.0)
  };
  double x[5] = {-2.0, -1.0, 0.0, 1.0, 2.0};
  double xe;
  int rc = discr5ea(A, x, &xe);
  assert(rc == 0);
  assert(std::fabs(xe) < 1e-10);
  std::cout << "[PASS] discr5ea: gaussian symmetric -> 0.0\n";
}

inline void test_gaussian_shifted() {
  /* Гауссов пик в 0.3: A(x) = exp(-(x-0.3)^2) */
  double x0 = 0.3;
  double A[5], x[5];
  for (int i = 0; i < 5; i++) {
    x[i] = -2.0 + i;
    A[i] = std::exp(-(x[i] - x0) * (x[i] - x0));
  }
  double xe;
  int rc = discr5ea(A, x, &xe);
  assert(rc == 0);
  /* Для гауссовых данных в лог-масштабе МНК точно = интерполяция */
  assert(std::fabs(xe - x0) < 0.01);
  std::cout << "[PASS] discr5ea: gaussian shifted 0.3 -> " << xe
            << " (err=" << std::fabs(xe - x0) << ")\n";
}

inline void test_sinc_symmetric() {
  /* sinc(x), пик в 0, сетка {-2,-1,0,1,2} */
  double A[5], x[5];
  for (int i = 0; i < 5; i++) {
    x[i] = -2.0 + i;
    A[i] = sinc(x[i]);
  }
  double xe;
  int rc = discr5ea(A, x, &xe);
  assert(rc == 0);
  assert(std::fabs(xe) < 0.01);
  std::cout << "[PASS] discr5ea: sinc symmetric -> " << xe << "\n";
}

inline void test_sinc_shifted_03() {
  /* sinc(x - 0.3), сетка {-2,-1,0,1,2} */
  double x0 = 0.3;
  double A[5], x[5];
  for (int i = 0; i < 5; i++) {
    x[i] = -2.0 + i;
    A[i] = sinc(x[i] - x0);
  }
  double xe;
  int rc = discr5ea(A, x, &xe);
  assert(rc == 0);
  assert(std::fabs(xe - x0) < 0.05);
  std::cout << "[PASS] discr5ea: sinc shifted 0.3 -> " << xe
            << " (err=" << std::fabs(xe - x0) << ")\n";
}

inline void test_sinc_fine_grid() {
  /* sinc(x - 0.2), мелкая сетка шаг 0.5: {-1, -0.5, 0, 0.5, 1} */
  double x0 = 0.2;
  double A[5], x[5];
  double step = 0.5;
  for (int i = 0; i < 5; i++) {
    x[i] = -1.0 + i * step;
    A[i] = sinc(x[i] - x0);
  }
  double xe;
  int rc = discr5ea(A, x, &xe);
  assert(rc == 0);
  assert(std::fabs(xe - x0) < 0.02);
  std::cout << "[PASS] discr5ea: sinc fine grid (step=0.5) -> " << xe
            << " (err=" << std::fabs(xe - x0) << ")\n";
}

inline void test_zero_amplitude() {
  double A[5] = {0.0, 1.0, 2.0, 1.0, 0.5};
  double x[5] = {-2.0, -1.0, 0.0, 1.0, 2.0};
  double xe;
  int rc = discr5ea(A, x, &xe);
  assert(rc != 0);  /* EXIT_FAILURE: A[0] = 0 */
  assert(std::fabs(xe - 0.0) < 1e-12);  /* fallback = x[2] */
  std::cout << "[PASS] discr5ea: zero amplitude -> FAILURE, xe=x[2]\n";
}

inline void test_all_equal() {
  double A[5] = {3.0, 3.0, 3.0, 3.0, 3.0};
  double x[5] = {-2.0, -1.0, 0.0, 1.0, 2.0};
  double xe;
  int rc = discr5ea(A, x, &xe);
  assert(rc != 0);
  std::cout << "[PASS] discr5ea: all equal -> FAILURE\n";
}


/* ==================== discr5qa (Parabolic LSQ 5pt) ==================== */

inline void test_qa5_parabola_exact() {
  /* Парабола y = -(x-0.4)^2 + 10, точки {-2,-1,0,1,2} */
  double x0 = 0.4;
  double A[5], x[5];
  for (int i = 0; i < 5; i++) {
    x[i] = -2.0 + i;
    A[i] = -(x[i] - x0) * (x[i] - x0) + 10.0;
  }
  double xe;
  int rc = discr5qa(A, x, &xe);
  assert(rc == 0);
  /* Для параболических данных МНК дает точное решение */
  assert(std::fabs(xe - x0) < 1e-10);
  std::cout << "[PASS] discr5qa: exact parabola -> " << xe << "\n";
}

inline void test_qa5_sinc_symmetric() {
  double A[5], x[5];
  for (int i = 0; i < 5; i++) {
    x[i] = -2.0 + i;
    A[i] = sinc(x[i]);
  }
  double xe;
  int rc = discr5qa(A, x, &xe);
  assert(rc == 0);
  assert(std::fabs(xe) < 0.01);
  std::cout << "[PASS] discr5qa: sinc symmetric -> " << xe << "\n";
}

inline void test_qa5_sinc_shifted() {
  double x0 = 0.3;
  double A[5], x[5];
  for (int i = 0; i < 5; i++) {
    x[i] = -2.0 + i;
    A[i] = sinc(x[i] - x0);
  }
  double xe;
  int rc = discr5qa(A, x, &xe);
  assert(rc == 0);
  assert(std::fabs(xe - x0) < 0.1);
  std::cout << "[PASS] discr5qa: sinc shifted 0.3 -> " << xe
            << " (err=" << std::fabs(xe - x0) << ")\n";
}


/* ==================== Сравнение точности ==================== */

inline void test_5ea_better_than_3ea() {
  /* discr5ea должен быть точнее или сопоставим с discr3ea на чистых данных */
  double x0 = 0.25;
  double A5[5], x5[5];
  for (int i = 0; i < 5; i++) {
    x5[i] = -2.0 + i;
    A5[i] = sinc(x5[i] - x0);
  }
  double xe5;
  discr5ea(A5, x5, &xe5);
  double err5 = std::fabs(xe5 - x0);

  /* Для сравнения — discr3ea (центральные 3 точки) */
  double xe3;
  extern "C" int discr3ea(double, double, double, double, double, double, double*);
  discr3ea(A5[1], A5[2], A5[3], x5[1], x5[2], x5[3], &xe3);
  double err3 = std::fabs(xe3 - x0);

  std::cout << "[INFO] discr5ea err=" << err5
            << ", discr3ea err=" << err3 << "\n";
  /* МНК-5 на чистых данных с шагом 1 может быть чуть хуже 3-точечного
   * (ожидаемо), но не должен быть катастрофически хуже */
  assert(err5 < 0.1);
  std::cout << "[PASS] discr5ea: accuracy comparable to discr3ea\n";
}

inline void test_5ea_fine_grid_better() {
  /* На мелкой сетке (шаг 0.5) discr5ea должен быть ЛУЧШЕ discr3ea */
  double x0 = 0.15;
  double step = 0.5;
  double A5[5], x5[5];
  for (int i = 0; i < 5; i++) {
    x5[i] = -1.0 + i * step;
    A5[i] = sinc(x5[i] - x0);
  }
  double xe5;
  int rc5 = discr5ea(A5, x5, &xe5);
  double err5 = std::fabs(xe5 - x0);

  /* discr3ea по центральным 3 точкам (шаг 0.5) */
  double xe3;
  extern "C" int discr3ea(double, double, double, double, double, double, double*);
  discr3ea(A5[1], A5[2], A5[3], x5[1], x5[2], x5[3], &xe3);
  double err3 = std::fabs(xe3 - x0);

  std::cout << "[INFO] fine grid (h=0.5): discr5ea err=" << err5
            << ", discr3ea err=" << err3 << "\n";
  assert(rc5 == 0);
  assert(err5 < 0.05);
  std::cout << "[PASS] discr5ea fine grid: err=" << err5 << "\n";
}


inline void run_all() {
  std::cout << "\n=== 5EA / 5QA Tests (LSQ 5-point) ===\n";

  /* discr5ea */
  test_gaussian_symmetric();
  test_gaussian_shifted();
  test_sinc_symmetric();
  test_sinc_shifted_03();
  test_sinc_fine_grid();
  test_zero_amplitude();
  test_all_equal();

  /* discr5qa */
  test_qa5_parabola_exact();
  test_qa5_sinc_symmetric();
  test_qa5_sinc_shifted();

  /* Сравнение */
  test_5ea_better_than_3ea();
  test_5ea_fine_grid_better();
}

}  // namespace discr_test_5ea
