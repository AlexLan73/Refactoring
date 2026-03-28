/**
 * @file test_discr_cg_gtest.cpp
 * @brief Google Test: дискриминатор центр тяжести (CG) на данных sinc(x)
 *
 * Функция ДН антенны близка к sinc(x) = sin(x)/x.
 * Экспериментальные данные — отсчёты sinc(x) в нескольких точках сетки.
 */

#include <gtest/gtest.h>
#include <cmath>

extern "C" {
#include "discrcg.h"
}

// --- Утилиты ---

/// sinc(x) = sin(x)/x, sinc(0) = 1
static double sinc(double x) {
  if (fabs(x) < 1e-15) return 1.0;
  return sin(x) / x;
}

// === discr2cg ===

TEST(Discr2CG, EqualAmplitudes) {
  // Равные амплитуды → середина
  double r = discr2cg(1.0, 1.0, 0.0, 1.0);
  EXPECT_NEAR(r, 0.5, 1e-12);
}

TEST(Discr2CG, DominantRight) {
  double r = discr2cg(1.0, 99.0, 0.0, 1.0);
  EXPECT_GT(r, 0.98);
  EXPECT_LT(r, 1.0);
}

TEST(Discr2CG, ZeroAmplitudes_ERR005) {
  // ERR-005: деление на 0 → возвращает середину
  double r = discr2cg(0.0, 0.0, 0.0, 1.0);
  EXPECT_NEAR(r, 0.5, 1e-12);
}

TEST(Discr2CG, SincData_Peak_at_0) {
  // sinc(x) с пиком в 0: отсчёты при x = -0.5, +0.5
  double A1 = sinc(-0.5);  // ~0.9589
  double A2 = sinc(0.5);   // ~0.9589
  double r = discr2cg(A1, A2, -0.5, 0.5);
  EXPECT_NEAR(r, 0.0, 1e-10) << "Symmetric sinc -> peak at 0";
}

TEST(Discr2CG, SincData_Peak_shifted) {
  // sinc(x - 0.2) с пиком в 0.2: отсчёты при x = -0.5, +0.5
  double x0 = 0.2;
  double A1 = sinc(-0.5 - x0);  // sinc(-0.7)
  double A2 = sinc(0.5 - x0);   // sinc(0.3)
  double r = discr2cg(A1, A2, -0.5, 0.5);
  // CG даёт грубую оценку, но направление верное
  EXPECT_GT(r, 0.0) << "Peak shifted right -> estimate > 0";
  EXPECT_LT(r, 0.5);
}

// === discr3cg ===

TEST(Discr3CG, Symmetric) {
  double r = discr3cg(1.0, 3.0, 1.0, -1.0, 0.0, 1.0);
  EXPECT_NEAR(r, 0.0, 1e-12);
}

TEST(Discr3CG, ZeroAmplitudes_ERR005) {
  double r = discr3cg(0.0, 0.0, 0.0, -1.0, 0.0, 1.0);
  EXPECT_NEAR(r, 0.0, 1e-12);
}

TEST(Discr3CG, SincData_Peak_at_0) {
  // sinc(x) отсчёты при x = -1, 0, +1
  double A1 = sinc(-1.0);  // ~0.8415
  double A2 = sinc(0.0);   // 1.0
  double A3 = sinc(1.0);   // ~0.8415
  double r = discr3cg(A1, A2, A3, -1.0, 0.0, 1.0);
  EXPECT_NEAR(r, 0.0, 1e-10) << "Symmetric sinc -> 0";
}

TEST(Discr3CG, SincData_Peak_at_03) {
  double x0 = 0.3;
  double A1 = sinc(-1.0 - x0);
  double A2 = sinc(0.0 - x0);
  double A3 = sinc(1.0 - x0);
  double r = discr3cg(A1, A2, A3, -1.0, 0.0, 1.0);
  EXPECT_NEAR(r, x0, 0.35) << "CG: coarse estimate near 0.3";
}

// === discrncg ===

TEST(DiscrNCG, SinglePeak) {
  double A[] = {0.1, 0.5, 10.0, 0.5, 0.1};
  double x[] = {-2.0, -1.0, 0.0, 1.0, 2.0};
  double r = discrncg(A, x, 5);
  EXPECT_NEAR(r, 0.0, 0.1);
}

TEST(DiscrNCG, SincData_5points) {
  // 5 отсчётов sinc(x) с шагом 0.5
  double x[] = {-1.0, -0.5, 0.0, 0.5, 1.0};
  double A[5];
  for (int i = 0; i < 5; i++) A[i] = sinc(x[i]);
  double r = discrncg(A, x, 5);
  EXPECT_NEAR(r, 0.0, 0.05) << "5-point sinc -> ~0";
}

TEST(DiscrNCG, ZeroAmplitudes_ERR005) {
  double A[] = {0.0, 0.0, 0.0};
  double x[] = {-1.0, 0.0, 1.0};
  double r = discrncg(A, x, 3);
  EXPECT_NEAR(r, 0.0, 1e-12);
}
