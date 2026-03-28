/**
 * @file test_discr_qa_gtest.cpp
 * @brief Google Test: квадратичная аппроксимация (QA) на данных sinc(x)
 */

#include <gtest/gtest.h>
#include <cmath>

extern "C" {
#include "discrqa.h"
}

static double sinc(double x) {
  if (fabs(x) < 1e-15) return 1.0;
  return sin(x) / x;
}

TEST(Discr3QA, SymmetricParabola) {
  // y = 3 - x² → A={2,3,2}, x={-1,0,1}
  double r = discr3qa(2.0, 3.0, 2.0, -1.0, 0.0, 1.0);
  EXPECT_NEAR(r, 0.0, 1e-12);
}

TEST(Discr3QA, ShiftedParabola) {
  // y = -(x-0.5)² + 3
  double r = discr3qa(0.75, 2.75, 2.75, -1.0, 0.0, 1.0);
  EXPECT_NEAR(r, 0.5, 1e-10);
}

TEST(Discr3QA, AllEqual) {
  double r = discr3qa(5.0, 5.0, 5.0, -1.0, 0.0, 1.0);
  EXPECT_NEAR(r, 0.0, 1e-12);
}

TEST(Discr3QA, A2_equals_A3) {
  double r = discr3qa(1.0, 5.0, 5.0, 0.0, 1.0, 2.0);
  EXPECT_NEAR(r, 1.5, 1e-12);
}

TEST(Discr3QA, SincData_Peak_at_0) {
  // sinc(x) при x = {-1, 0, +1}
  double A1 = sinc(-1.0);
  double A2 = sinc(0.0);
  double A3 = sinc(1.0);
  double r = discr3qa(A1, A2, A3, -1.0, 0.0, 1.0);
  EXPECT_NEAR(r, 0.0, 1e-10) << "sinc symmetric -> 0";
}

TEST(Discr3QA, SincData_Peak_at_02) {
  double x0 = 0.2;
  double A1 = sinc(-1.0 - x0);
  double A2 = sinc(0.0 - x0);
  double A3 = sinc(1.0 - x0);
  double r = discr3qa(A1, A2, A3, -1.0, 0.0, 1.0);
  // QA на sinc даёт хорошую оценку (±0.1 шага)
  EXPECT_NEAR(r, x0, 0.15) << "QA sinc peak at 0.2";
}

TEST(Discr3QA, SincData_Peak_at_04_fine_grid) {
  // Мелкая сетка: шаг 0.5
  double x0 = 0.4;
  double A1 = sinc(-0.5 - x0);
  double A2 = sinc(0.0 - x0);
  double A3 = sinc(0.5 - x0);
  double r = discr3qa(A1, A2, A3, -0.5, 0.0, 0.5);
  EXPECT_NEAR(r, x0, 0.1) << "QA fine grid sinc peak at 0.4";
}
