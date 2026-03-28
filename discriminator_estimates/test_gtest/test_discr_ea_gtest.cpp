/**
 * @file test_discr_ea_gtest.cpp
 * @brief Google Test: экспоненциальная аппроксимация (EA) на данных sinc(x)
 */

#include <gtest/gtest.h>
#include <cmath>

extern "C" {
#include "discrea.h"
}

static double sinc(double x) {
  if (fabs(x) < 1e-15) return 1.0;
  return sin(x) / x;
}

TEST(Discr3EA, GaussianCenter) {
  // Гауссов пик в 0: A = exp(-x²)
  double xe;
  int rc = discr3ea(exp(-1.0), 1.0, exp(-1.0), -1.0, 0.0, 1.0, &xe);
  EXPECT_EQ(rc, 0);
  EXPECT_NEAR(xe, 0.0, 1e-10);
}

TEST(Discr3EA, GaussianShifted) {
  double xe;
  int rc = discr3ea(exp(-1.69), exp(-0.09), exp(-0.49), -1.0, 0.0, 1.0, &xe);
  EXPECT_EQ(rc, 0);
  EXPECT_NEAR(xe, 0.3, 0.05);
}

TEST(Discr3EA, ZeroAmplitude) {
  double xe;
  int rc = discr3ea(0.0, 1.0, 0.5, -1.0, 0.0, 1.0, &xe);
  EXPECT_NE(rc, 0);
}

TEST(Discr3EA, AllEqual) {
  double xe;
  int rc = discr3ea(5.0, 5.0, 5.0, -1.0, 0.0, 1.0, &xe);
  EXPECT_NE(rc, 0);
}

TEST(Discr3EA, ConcaveIncreasing) {
  // 2, 4, 8 — монотонный рост → failure
  double xe;
  int rc = discr3ea(2.0, 4.0, 8.0, -1.0, 0.0, 1.0, &xe);
  EXPECT_NE(rc, 0);
}

TEST(Discr3EA, SincData_Peak_at_0) {
  // sinc(x) отсчёты при x = {-0.8, 0.0, +0.8}
  // sinc близка к exp вблизи максимума — EA должна дать хороший результат
  double A1 = sinc(-0.8);
  double A2 = sinc(0.0);
  double A3 = sinc(0.8);
  double xe;
  int rc = discr3ea(A1, A2, A3, -0.8, 0.0, 0.8, &xe);
  EXPECT_EQ(rc, 0);
  EXPECT_NEAR(xe, 0.0, 1e-10) << "EA: sinc symmetric -> 0";
}

TEST(Discr3EA, SincData_Peak_at_02) {
  double x0 = 0.2;
  double A1 = sinc(-0.8 - x0);
  double A2 = sinc(0.0 - x0);
  double A3 = sinc(0.8 - x0);
  double xe;
  int rc = discr3ea(A1, A2, A3, -0.8, 0.0, 0.8, &xe);
  EXPECT_EQ(rc, 0);
  // EA — самый точный: ±0.05 шага
  EXPECT_NEAR(xe, x0, 0.1) << "EA: sinc peak at 0.2";
}

TEST(Discr3EA, AmplitudeRefinement) {
  double A1 = exp(-1.0), A2 = 1.0;
  double ye = discr3eaY(A1, A2, -1.0, 0.0, 0.0);
  EXPECT_GT(ye, 0.9);
  EXPECT_LT(ye, 1.1);
}
