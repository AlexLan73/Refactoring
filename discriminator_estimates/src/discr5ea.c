/**
 * @file    discr5ea.c
 * @author  Кодо (AI), Alex
 * @date    03.04.2026
 * @brief   КППО / ТЗК. Дискриминатор — МНК-гауссова аппроксимация по 5 точкам.
 *
 * Реализует два метода МНК по 5 равноотстоящим точкам:
 *   - discr5ea: гауссов (в лог-масштабе)
 *   - discr5qa: параболический (в линейном масштабе)
 *
 * Математика:
 *   Нормируем координаты xi -> {-2, -1, 0, 1, 2}.
 *   Для переопределённой системы y = a*x^2 + b*x + c (5 уравнений, 3 неизвестных)
 *   нормальные уравнения (A^T * A) * beta = A^T * y дают замкнутые формулы:
 *
 *     a = (2*y1 - y2 - 2*y3 - y4 + 2*y5) / 14
 *     b = (-2*y1 - y2 + y4 + 2*y5) / 10
 *     xe = -b / (2*a)   (в нормированных единицах)
 *
 *   Затем обратная нормировка: xe_real = x3 + h * xe_norm
 */

#include "discr5ea.h"
#include <float.h>
#include <math.h>
#include <stdlib.h>

/**
 * Внутренняя функция: МНК-параболическая оценка вершины по 5 значениям yi.
 * Координаты предполагаются нормированными {-2, -1, 0, 1, 2}.
 *
 * @param y    массив из 5 значений (амплитуды или логарифмы)
 * @param peak [out] смещение вершины в нормированных координатах
 * @return     EXIT_SUCCESS или EXIT_FAILURE
 */
static int lsq5_peak(const double y[5], double *peak)
{
  /* МНК-коэффициенты параболы y = a*t^2 + b*t + c
   * для t = {-2, -1, 0, 1, 2} */
  double a = (2.0 * y[0] - y[1] - 2.0 * y[2] - y[3] + 2.0 * y[4]) / 14.0;
  double b = (-2.0 * y[0] - y[1] + y[3] + 2.0 * y[4]) / 10.0;

  /* Парабола вогнутая (a < 0) — есть максимум */
  if (a > -DBL_EPSILON) {
    *peak = 0.0;
    return EXIT_FAILURE;
  }

  *peak = -b / (2.0 * a);

  /* Ограничение: вершина не дальше ±2 шагов от центра */
  if (*peak < -2.0)
    *peak = -2.0;
  else if (*peak > 2.0)
    *peak = 2.0;

  return EXIT_SUCCESS;
}


int discr5ea(const double A[5], const double x[5], double *xe)
{
  double z[5];
  double h, peak;
  int i, rc;

  /* Шаг сетки (берём из первых двух точек) */
  h = x[1] - x[0];
  if (fabs(h) < DBL_EPSILON) {
    *xe = x[2];
    return EXIT_FAILURE;
  }

  /* Проверка: все амплитуды положительны */
  for (i = 0; i < 5; i++) {
    if (A[i] < DBL_EPSILON) {
      *xe = x[2];
      return EXIT_FAILURE;
    }
  }

  /* Проверка: не все равны */
  {
    int all_equal = 1;
    for (i = 1; i < 5; i++) {
      if (fabs(A[i] - A[0]) > DBL_EPSILON) {
        all_equal = 0;
        break;
      }
    }
    if (all_equal) {
      *xe = x[2];
      return EXIT_FAILURE;
    }
  }

  /* Логарифмирование */
  for (i = 0; i < 5; i++) {
    z[i] = log(A[i]);
  }

  /* МНК-оценка вершины параболы в лог-масштабе */
  rc = lsq5_peak(z, &peak);

  /* Обратная нормировка: центр = x[2], шаг = h */
  *xe = x[2] + h * peak;

  return rc;
}


int discr5qa(const double A[5], const double x[5], double *xe)
{
  double h, peak;
  int rc;

  /* Шаг сетки */
  h = x[1] - x[0];
  if (fabs(h) < DBL_EPSILON) {
    *xe = x[2];
    return EXIT_FAILURE;
  }

  /* Проверка: не все равны */
  {
    int all_equal = 1;
    int i;
    for (i = 1; i < 5; i++) {
      if (fabs(A[i] - A[0]) > DBL_EPSILON) {
        all_equal = 0;
        break;
      }
    }
    if (all_equal) {
      *xe = x[2];
      return EXIT_FAILURE;
    }
  }

  /* МНК-оценка вершины параболы в линейном масштабе */
  rc = lsq5_peak(A, &peak);

  /* Обратная нормировка */
  *xe = x[2] + h * peak;

  return rc;
}
