/**
 * @file    discrsd.c
 * @author  Федоров С.А.
 * @date    07.05.2010
 * @brief   КППО / ТЗК. Дискриминатор — суммарно-разностный (Sum-Difference).
 *
 * Рефакторинг: Кодо, 2026-03-28
 * Изменения:
 *   - ERR-005: добавлена защита от деления на 0 (A2+A1=0)
 *   - STYLE: единые 2-пробельные отступы
 */

#include "discrsd.h"
#include <math.h>
#include <float.h>

/**
 * @brief Двухточечный дискриминатор, суммарно-разностный.
 *
 * Формулы:
 *   xc = (x1 + x2) / 2
 *   dx = c * (A2 - A1) / (A2 + A1)
 *   xe = xc + dx
 *
 * @param c   коэффициент суммарно-разностного дискриминатора
 * @param A1  амплитуда первой точки
 * @param A2  амплитуда второй точки
 * @param x1  координата первой точки
 * @param x2  координата второй точки
 * @return    оценка координаты; при A1+A2=0 возвращает середину (x1+x2)/2
 */
double discr2sd(double c, double A1, double A2,
                double x1, double x2)
{
  double xc = (x1 + x2) * 0.5;
  double sum = A2 + A1;

  if (fabs(sum) < DBL_EPSILON)
    return xc;

  double dx = c * ((A2 - A1) / sum);
  return xc + dx;
}
