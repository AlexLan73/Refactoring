#pragma once
/**
 * @file test_discr_cg.hpp
 * @brief Тесты: дискриминатор центр тяжести (CG)
 */

extern "C" {
#include "discrcg.h"
}
#include <cassert>
#include <cmath>
#include <iostream>

namespace discr_test_cg {

inline void test_2point_equal() {
  double r = discr2cg(1.0, 1.0, 0.0, 1.0);
  assert(fabs(r - 0.5) < 1e-12);
  std::cout << "[PASS] discr2cg: equal amplitudes -> midpoint\n";
}

inline void test_2point_dominant() {
  double r = discr2cg(1.0, 99.0, 0.0, 1.0);
  assert(r > 0.98 && r < 1.0);
  std::cout << "[PASS] discr2cg: dominant A2 -> near x2\n";
}

inline void test_2point_zero_amplitudes() {
  double r = discr2cg(0.0, 0.0, 0.0, 1.0);
  assert(fabs(r - 0.5) < 1e-12);  // ERR-005 fix: midpoint
  std::cout << "[PASS] discr2cg: zero amplitudes -> midpoint (ERR-005)\n";
}

inline void test_3point_symmetric() {
  double r = discr3cg(1.0, 3.0, 1.0, -1.0, 0.0, 1.0);
  assert(fabs(r - 0.0) < 1e-12);
  std::cout << "[PASS] discr3cg: symmetric -> center\n";
}

inline void test_3point_zero_amplitudes() {
  double r = discr3cg(0.0, 0.0, 0.0, -1.0, 0.0, 1.0);
  assert(fabs(r - 0.0) < 1e-12);  // returns x2
  std::cout << "[PASS] discr3cg: zero amplitudes -> x2 (ERR-005)\n";
}

inline void test_npoint_single_peak() {
  double A[] = {0.1, 0.5, 10.0, 0.5, 0.1};
  double x[] = {-2.0, -1.0, 0.0, 1.0, 2.0};
  double r = discrncg(A, x, 5);
  assert(fabs(r) < 0.1);  // close to 0
  std::cout << "[PASS] discrncg: single peak -> near center\n";
}

inline void test_npoint_zero_amplitudes() {
  double A[] = {0.0, 0.0, 0.0};
  double x[] = {-1.0, 0.0, 1.0};
  double r = discrncg(A, x, 3);
  assert(fabs(r - 0.0) < 1e-12);  // returns x[N/2]
  std::cout << "[PASS] discrncg: zero amplitudes -> x[N/2] (ERR-005)\n";
}

inline void run_all() {
  std::cout << "\n=== CG Tests ===\n";
  test_2point_equal();
  test_2point_dominant();
  test_2point_zero_amplitudes();
  test_3point_symmetric();
  test_3point_zero_amplitudes();
  test_npoint_single_peak();
  test_npoint_zero_amplitudes();
}

}  // namespace discr_test_cg
