#pragma once
/**
 * @file test_discr_qa.hpp
 * @brief Тесты: квадратичная аппроксимация (QA)
 */

extern "C" {
#include "discrqa.h"
}
#include <cassert>
#include <cmath>
#include <iostream>

namespace discr_test_qa {

inline void test_symmetric_peak() {
  // Парабола с вершиной в 0: y = 3 - x^2 => A(-1)=2, A(0)=3, A(1)=2
  double r = discr3qa(2.0, 3.0, 2.0, -1.0, 0.0, 1.0);
  assert(fabs(r - 0.0) < 1e-12);
  std::cout << "[PASS] discr3qa: symmetric parabola -> 0.0\n";
}

inline void test_shifted_peak() {
  // Парабола y = -(x-0.5)^2 + 3 => A(-1)=0.75, A(0)=2.75, A(1)=2.75
  double r = discr3qa(0.75, 2.75, 2.75, -1.0, 0.0, 1.0);
  assert(fabs(r - 0.5) < 1e-10);
  std::cout << "[PASS] discr3qa: shifted peak -> 0.5\n";
}

inline void test_all_equal() {
  double r = discr3qa(5.0, 5.0, 5.0, -1.0, 0.0, 1.0);
  assert(fabs(r - 0.0) < 1e-12);  // A1=A2=A3 -> x2
  std::cout << "[PASS] discr3qa: all equal -> x2\n";
}

inline void test_a2_equals_a3() {
  double r = discr3qa(1.0, 5.0, 5.0, 0.0, 1.0, 2.0);
  assert(fabs(r - 1.5) < 1e-12);  // A2=A3, A1<A2 -> (x2+x3)/2
  std::cout << "[PASS] discr3qa: A2=A3, A1<A2 -> midpoint x2,x3\n";
}

inline void test_a1_equals_a2() {
  double r = discr3qa(5.0, 5.0, 1.0, 0.0, 1.0, 2.0);
  assert(fabs(r - 0.5) < 1e-12);  // A1=A2, A3<A2 -> (x1+x2)/2
  std::cout << "[PASS] discr3qa: A1=A2, A3<A2 -> midpoint x1,x2\n";
}

inline void run_all() {
  std::cout << "\n=== QA Tests ===\n";
  test_symmetric_peak();
  test_shifted_peak();
  test_all_equal();
  test_a2_equals_a3();
  test_a1_equals_a2();
}

}  // namespace discr_test_qa
