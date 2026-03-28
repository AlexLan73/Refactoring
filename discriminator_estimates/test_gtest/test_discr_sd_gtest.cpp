/**
 * @file test_discr_sd_gtest.cpp
 * @brief Google Test: суммарно-разностный дискриминатор (SD) на данных sinc(x)
 */

#include <gtest/gtest.h>
#include <cmath>

extern "C" {
#include "discrsd.h"
}

static double sinc(double x) {
  if (fabs(x) < 1e-15) return 1.0;
  return sin(x) / x;
}

TEST(Discr2SD, EqualAmplitudes) {
  double r = discr2sd(1.0, 1.0, 1.0, 0.0, 1.0);
  EXPECT_NEAR(r, 0.5, 1e-12);
}

TEST(Discr2SD, ShiftedRight) {
  // xc=0.5, dx = 1.0*(3-1)/(3+1) = 0.5 → xe = 1.0
  double r = discr2sd(1.0, 1.0, 3.0, 0.0, 1.0);
  EXPECT_NEAR(r, 1.0, 1e-12);
}

TEST(Discr2SD, ZeroAmplitudes_ERR005) {
  double r = discr2sd(1.0, 0.0, 0.0, 0.0, 1.0);
  EXPECT_NEAR(r, 0.5, 1e-12);
}

TEST(Discr2SD, SincData_Peak_at_0) {
  // sinc(x) при x = -0.5, +0.5, коэффициент c = 1.0
  double A1 = sinc(-0.5);
  double A2 = sinc(0.5);
  // Равные → dx=0 → xe = середина = 0
  double r = discr2sd(1.0, A1, A2, -0.5, 0.5);
  EXPECT_NEAR(r, 0.0, 1e-10);
}

TEST(Discr2SD, SincData_Peak_at_02) {
  double x0 = 0.2;
  double A1 = sinc(-0.5 - x0);
  double A2 = sinc(0.5 - x0);
  double r = discr2sd(0.5, A1, A2, -0.5, 0.5);
  EXPECT_GT(r, 0.0) << "Peak right -> estimate > 0";
}
