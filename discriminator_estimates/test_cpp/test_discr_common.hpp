#pragma once
/**
 * @file test_discr_common.hpp
 * @brief Тесты: обёртки (discr2, discr3_, conv3to2, checkuse3d)
 */

extern "C" {
#include "discr_common.h"
#include "discrcg.h"
}
#include <cassert>
#include <cmath>
#include <iostream>

namespace discr_test_common {

inline void test_discr2_basic() {
  double maz[2][2] = {{0.0, 1.0}, {0.0, 1.0}};
  double mel[2][2] = {{0.0, 0.0}, {1.0, 1.0}};
  double mval[2][2] = {{1.0, 3.0}, {2.0, 4.0}};
  double az, el, val;

  int rc = discr2(maz, mel, mval, &az, &el, &val);
  assert(rc == 0);
  assert(val == 4.0);  // max = mval[1][1]
  std::cout << "[PASS] discr2: basic (ERR-001 fix)\n";
}

inline void test_discr3_qa_no_side_effect() {
  /* ERR-003: discr3 must NOT modify input arrays */
  double maz_data[3][3] = {{-1, 0, 1}, {-1, 0, 1}, {-1, 0, 1}};
  double mel_data[3][3] = {{-1, -1, -1}, {0, 0, 0}, {1, 1, 1}};
  double mval[3][3] = {{1, 2, 1}, {2, 5, 2}, {1, 2, 1}};
  double az, el, val;

  /* Сохраняем копию для сравнения */
  double maz_before = maz_data[0][0];

  int rc = discr3_(maz_data, mel_data, mval, DT_QA, 0.1, 0.03, &az, &el, &val);
  assert(rc == 0);

  /* Проверяем что входные данные НЕ изменились */
  assert(fabs(maz_data[0][0] - maz_before) < 1e-15);
  std::cout << "[PASS] discr3_: no side effect on maz (ERR-003 fix)\n";
}

inline void test_discr3_cg() {
  /* ERR-006: DT_CG теперь поддерживается */
  double maz_data[3][3] = {{-1, 0, 1}, {-1, 0, 1}, {-1, 0, 1}};
  double mel_data[3][3] = {{-1, -1, -1}, {0, 0, 0}, {1, 1, 1}};
  double mval[3][3] = {{1, 2, 1}, {2, 5, 2}, {1, 2, 1}};
  double az, el, val;

  int rc = discr3_(maz_data, mel_data, mval, DT_CG, 0.1, 0.03, &az, &el, &val);
  assert(rc == 0);
  assert(fabs(az) < 0.5);  // near center
  assert(fabs(el) < 0.5);
  std::cout << "[PASS] discr3_: DT_CG supported (ERR-006 fix)\n";
}

inline void test_checkuse3d_positive() {
  double maz_data[3][3] = {{-1, 0, 1}, {-1, 0, 1}, {-1, 0, 1}};
  double mel_data[3][3] = {{-1, -1, -1}, {0, 0, 0}, {1, 1, 1}};
  double mval[3][3] = {{1, 2, 1}, {2, 5, 2}, {1, 2, 1}};
  double *pmaz[3] = {maz_data[0], maz_data[1], maz_data[2]};
  double *pmel[3] = {mel_data[0], mel_data[1], mel_data[2]};
  double *pmval[3] = {mval[0], mval[1], mval[2]};

  assert(checkuse3d(pmaz, pmel, pmval, 3, 3) == 1);
  std::cout << "[PASS] checkuse3d: all positive -> 1\n";
}

inline void test_checkuse3d_zero() {
  double maz_data[3][3] = {{-1, 0, 1}, {-1, 0, 1}, {-1, 0, 1}};
  double mel_data[3][3] = {{-1, -1, -1}, {0, 0, 0}, {1, 1, 1}};
  double mval[3][3] = {{1, 0, 1}, {2, 5, 2}, {1, 2, 1}};  // zero at [0][1]
  double *pmaz[3] = {maz_data[0], maz_data[1], maz_data[2]};
  double *pmel[3] = {mel_data[0], mel_data[1], mel_data[2]};
  double *pmval[3] = {mval[0], mval[1], mval[2]};

  assert(checkuse3d(pmaz, pmel, pmval, 3, 3) == 0);
  std::cout << "[PASS] checkuse3d: has zero -> 0\n";
}

inline void test_conv3to2() {
  double maz3[3][3] = {{0,1,2}, {0,1,2}, {0,1,2}};
  double mel3[3][3] = {{0,0,0}, {1,1,1}, {2,2,2}};
  double mval3[3][3] = {{1,1,1}, {1,1,10}, {1,1,9}};  // max at [1][2]
  double maz2[2][2], mel2[2][2], mval2[2][2];

  int rc = conv3to2(maz3, mel3, mval3, maz2, mel2, mval2);
  assert(rc == 0);
  // best quadrant should contain [1][2] (value 10)
  double sum = mval2[0][0] + mval2[0][1] + mval2[1][0] + mval2[1][1];
  assert(sum > 20.0);  // quadrant with 10 and 9
  std::cout << "[PASS] conv3to2: picks best quadrant (ERR-001 fix)\n";
}

inline void run_all() {
  std::cout << "\n=== Common Tests ===\n";
  test_discr2_basic();
  test_discr3_qa_no_side_effect();
  test_discr3_cg();
  test_checkuse3d_positive();
  test_checkuse3d_zero();
  test_conv3to2();
}

}  // namespace discr_test_common
