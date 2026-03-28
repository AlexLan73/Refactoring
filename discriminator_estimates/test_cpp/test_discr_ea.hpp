#pragma once
/**
 * @file test_discr_ea.hpp
 * @brief Тесты: экспоненциальная аппроксимация (EA)
 */

extern "C" {
#include "discrea.h"
}
#include <cassert>
#include <cmath>
#include <iostream>

namespace discr_test_ea {

inline void test_gaussian_peak_center() {
  // Гауссов пик в 0: A = exp(-x^2) => A(-1)=0.368, A(0)=1.0, A(1)=0.368
  double A1 = exp(-1.0), A2 = 1.0, A3 = exp(-1.0);
  double xe;
  int rc = discr3ea(A1, A2, A3, -1.0, 0.0, 1.0, &xe);
  assert(rc == 0);
  assert(fabs(xe) < 1e-10);
  std::cout << "[PASS] discr3ea: gaussian center -> 0.0\n";
}

inline void test_gaussian_peak_shifted() {
  // Гауссов пик в 0.3: A(x) = exp(-(x-0.3)^2)
  double A1 = exp(-1.69), A2 = exp(-0.09), A3 = exp(-0.49);
  double xe;
  int rc = discr3ea(A1, A2, A3, -1.0, 0.0, 1.0, &xe);
  assert(rc == 0);
  assert(fabs(xe - 0.3) < 0.05);
  std::cout << "[PASS] discr3ea: gaussian shifted -> ~0.3\n";
}

inline void test_zero_amplitude() {
  double xe;
  int rc = discr3ea(0.0, 1.0, 0.5, -1.0, 0.0, 1.0, &xe);
  assert(rc != 0);  // EXIT_FAILURE
  assert(fabs(xe - 0.0) < 1e-12);  // x2
  std::cout << "[PASS] discr3ea: zero amplitude -> FAILURE, xe=x2\n";
}

inline void test_all_equal() {
  double xe;
  int rc = discr3ea(5.0, 5.0, 5.0, -1.0, 0.0, 1.0, &xe);
  assert(rc != 0);  // EXIT_FAILURE
  std::cout << "[PASS] discr3ea: all equal -> FAILURE\n";
}

inline void test_concave_increasing() {
  // Вогнутость: 2, 4, 8 (монотонный рост)
  double xe;
  int rc = discr3ea(2.0, 4.0, 8.0, -1.0, 0.0, 1.0, &xe);
  assert(rc != 0);  // EXIT_FAILURE
  std::cout << "[PASS] discr3ea: concave increasing -> FAILURE\n";
}

inline void test_amplitude_refinement() {
  double A1 = exp(-1.0), A2 = 1.0;
  double ye = discr3eaY(A1, A2, -1.0, 0.0, 0.0);
  // xe=0, A2=1.0 -> ye should be close to 1.0
  assert(ye > 0.9 && ye < 1.1);
  std::cout << "[PASS] discr3eaY: amplitude refinement\n";
}

inline void run_all() {
  std::cout << "\n=== EA Tests ===\n";
  test_gaussian_peak_center();
  test_gaussian_peak_shifted();
  test_zero_amplitude();
  test_all_equal();
  test_concave_increasing();
  test_amplitude_refinement();
}

}  // namespace discr_test_ea
