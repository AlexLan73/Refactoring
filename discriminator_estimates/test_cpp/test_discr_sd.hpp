#pragma once
/**
 * @file test_discr_sd.hpp
 * @brief Тесты: суммарно-разностный дискриминатор (SD)
 */

extern "C" {
#include "discrsd.h"
}
#include <cassert>
#include <cmath>
#include <iostream>

namespace discr_test_sd {

inline void test_equal_amplitudes() {
  double r = discr2sd(1.0, 1.0, 1.0, 0.0, 1.0);
  assert(fabs(r - 0.5) < 1e-12);  // dx=0 -> midpoint
  std::cout << "[PASS] discr2sd: equal amplitudes -> midpoint\n";
}

inline void test_shifted_right() {
  double r = discr2sd(1.0, 1.0, 3.0, 0.0, 1.0);
  // xc=0.5, dx=1.0*(3-1)/(3+1)=0.5, xe=1.0
  assert(fabs(r - 1.0) < 1e-12);
  std::cout << "[PASS] discr2sd: shifted right\n";
}

inline void test_zero_amplitudes() {
  double r = discr2sd(1.0, 0.0, 0.0, 0.0, 1.0);
  assert(fabs(r - 0.5) < 1e-12);  // ERR-005 fix: midpoint
  std::cout << "[PASS] discr2sd: zero amplitudes -> midpoint (ERR-005)\n";
}

inline void run_all() {
  std::cout << "\n=== SD Tests ===\n";
  test_equal_amplitudes();
  test_shifted_right();
  test_zero_amplitudes();
}

}  // namespace discr_test_sd
