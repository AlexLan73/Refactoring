/**
 * @file    discrcg.c
 * @author  Федоров С.А.
 * @date    07.05.2010
 * @brief   КППО / ТЗК. Дискриминатор — центр тяжести (Center of Gravity).
 *
 * Рефакторинг: Кодо, 2026-03-28
 * Изменения:
 *   - ERR-005: добавлена защита от деления на 0 (A1+A2=0, As=0)
 *   - STYLE: единые 2-пробельные отступы, пробелы вокруг операторов
 */

#include "discrcg.h"
#include <math.h>
#include <float.h>

/**
 * @brief Двухточечный дискриминатор, центр тяжести.
 *
 * Формула: xe = (A1*x1 + A2*x2) / (A1 + A2)
 *
 * @param A1  амплитуда первой точки
 * @param A2  амплитуда второй точки
 * @param x1  координата первой точки
 * @param x2  координата второй точки
 * @return    оценка координаты; при A1+A2=0 возвращает середину (x1+x2)/2
 */
double discr2cg(double A1, double A2,
                double x1, double x2)
{
  double sum = A1 + A2;
  if (fabs(sum) < DBL_EPSILON)
    return (x1 + x2) * 0.5;
  return (A1 * x1 + A2 * x2) / sum;
}

/**
 * @brief Трехточечный дискриминатор, центр тяжести.
 *
 * Формула: xe = (A1*x1 + A2*x2 + A3*x3) / (A1 + A2 + A3)
 *
 * @param A1  амплитуда первой точки
 * @param A2  амплитуда второй точки
 * @param A3  амплитуда третьей точки
 * @param x1  координата первой точки
 * @param x2  координата второй точки
 * @param x3  координата третьей точки
 * @return    оценка координаты; при сумме=0 возвращает x2 (центральная точка)
 */
double discr3cg(double A1, double A2, double A3,
                double x1, double x2, double x3)
{
  double sum = A1 + A2 + A3;
  if (fabs(sum) < DBL_EPSILON)
    return x2;
  return (A1 * x1 + A2 * x2 + A3 * x3) / sum;
}

/**
 * @brief Дискриминатор для произвольного числа точек, центр тяжести.
 *
 * Формула: xe = sum(A[i]*x[i]) / sum(A[i])
 *
 * @param A   массив амплитуд точек (N элементов)
 * @param x   массив координат точек (N элементов)
 * @param N   число точек
 * @return    оценка координаты; при sum(A)=0 возвращает x[N/2]
 */
double discrncg(const double *A, const double *x, unsigned int N)
{
  unsigned int n;
  double Axs = 0.0, As = 0.0;

  for (n = 0; n < N; n++) {
    As += A[n];
    Axs += A[n] * x[n];
  }

  if (fabs(As) < DBL_EPSILON) {
    if (N > 0)
      return x[N / 2];
    return 0.0;
  }
  return Axs / As;
}
