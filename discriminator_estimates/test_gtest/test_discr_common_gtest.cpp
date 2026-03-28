/**
 * @file test_discr_common_gtest.cpp
 * @brief Google Test: обёртки (discr2, discr3_, conv3to2, checkuse3d)
 */

#include <gtest/gtest.h>
#include <cmath>

extern "C" {
#include "discr_common.h"
#include "discrcg.h"
}

static double sinc(double x) {
  if (fabs(x) < 1e-15) return 1.0;
  return sin(x) / x;
}

TEST(Discr2, BasicCG_ERR001) {
  double maz[2][2]  = {{0.0, 1.0}, {0.0, 1.0}};
  double mel[2][2]  = {{0.0, 0.0}, {1.0, 1.0}};
  double mval[2][2] = {{1.0, 3.0}, {2.0, 4.0}};
  double az, el, val;
  int rc = discr2(maz, mel, mval, &az, &el, &val);
  EXPECT_EQ(rc, 0);
  EXPECT_DOUBLE_EQ(val, 4.0);
}

TEST(Discr3, QA_NoSideEffect_ERR003) {
  double maz[3][3]  = {{-1, 0, 1}, {-1, 0, 1}, {-1, 0, 1}};
  double mel[3][3]  = {{-1, -1, -1}, {0, 0, 0}, {1, 1, 1}};
  double mval[3][3] = {{1, 2, 1}, {2, 5, 2}, {1, 2, 1}};
  double az, el, val;
  double maz_before = maz[0][0];

  int rc = discr3_(maz, mel, mval, DT_QA, 0.1, 0.03, &az, &el, &val);
  EXPECT_EQ(rc, 0);
  EXPECT_DOUBLE_EQ(maz[0][0], maz_before) << "ERR-003: input must not change";
}

TEST(Discr3, CG_Supported_ERR006) {
  double maz[3][3]  = {{-1, 0, 1}, {-1, 0, 1}, {-1, 0, 1}};
  double mel[3][3]  = {{-1, -1, -1}, {0, 0, 0}, {1, 1, 1}};
  double mval[3][3] = {{1, 2, 1}, {2, 5, 2}, {1, 2, 1}};
  double az, el, val;

  int rc = discr3_(maz, mel, mval, DT_CG, 0.1, 0.03, &az, &el, &val);
  EXPECT_EQ(rc, 0);
  EXPECT_NEAR(az, 0.0, 0.5);
  EXPECT_NEAR(el, 0.0, 0.5);
}

TEST(Discr3, SincData3x3_QA) {
  // sinc(x)*sinc(y) отсчёты на сетке 3x3, пик в (0,0)
  double maz[3][3], mel[3][3], mval[3][3];
  double coords[] = {-1.0, 0.0, 1.0};
  for (int i = 0; i < 3; i++)
    for (int j = 0; j < 3; j++) {
      maz[i][j] = coords[j];
      mel[i][j] = coords[i];
      mval[i][j] = fabs(sinc(coords[j]) * sinc(coords[i]));
    }
  double az, el, val;
  int rc = discr3_(maz, mel, mval, DT_QA, 1.0, 2.0 * M_PI, &az, &el, &val);
  EXPECT_EQ(rc, 0);
  EXPECT_NEAR(az, 0.0, 0.2) << "QA sinc 3x3 -> az~0";
  EXPECT_NEAR(el, 0.0, 0.2) << "QA sinc 3x3 -> el~0";
}

TEST(CheckUse3D, AllPositive) {
  double maz[3][3] = {{-1,0,1},{-1,0,1},{-1,0,1}};
  double mel[3][3] = {{-1,-1,-1},{0,0,0},{1,1,1}};
  double mval[3][3] = {{1,2,1},{2,5,2},{1,2,1}};
  double *pmaz[3] = {maz[0], maz[1], maz[2]};
  double *pmel[3] = {mel[0], mel[1], mel[2]};
  double *pmval[3] = {mval[0], mval[1], mval[2]};
  EXPECT_EQ(checkuse3d(pmaz, pmel, pmval, 3, 3), 1);
}

TEST(CheckUse3D, HasZero) {
  double maz[3][3] = {{-1,0,1},{-1,0,1},{-1,0,1}};
  double mel[3][3] = {{-1,-1,-1},{0,0,0},{1,1,1}};
  double mval[3][3] = {{1,0,1},{2,5,2},{1,2,1}};
  double *pmaz[3] = {maz[0], maz[1], maz[2]};
  double *pmel[3] = {mel[0], mel[1], mel[2]};
  double *pmval[3] = {mval[0], mval[1], mval[2]};
  EXPECT_EQ(checkuse3d(pmaz, pmel, pmval, 3, 3), 0);
}

TEST(Conv3to2, BestQuadrant_ERR001) {
  double maz3[3][3] = {{0,1,2},{0,1,2},{0,1,2}};
  double mel3[3][3] = {{0,0,0},{1,1,1},{2,2,2}};
  double mval3[3][3] = {{1,1,1},{1,1,10},{1,1,9}};
  double maz2[2][2], mel2[2][2], mval2[2][2];

  int rc = conv3to2(maz3, mel3, mval3, maz2, mel2, mval2);
  EXPECT_EQ(rc, 0);
  double sum = mval2[0][0] + mval2[0][1] + mval2[1][0] + mval2[1][1];
  EXPECT_GT(sum, 20.0);
}
