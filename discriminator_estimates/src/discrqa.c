/**
 * @file    discrqa.c
 * @author  Федоров С.А.
 * @date    07.05.2010
 * @brief   КППО / ТЗК. Дискриминатор — квадратичная аппроксимация (Quadratic).
 *
 * Рефакторинг: Кодо, 2026-03-28
 * Изменения:
 *   - ERR-004: FLT_EPSILON заменён на DBL_EPSILON для double
 *   - STYLE-001: табуляции заменены на 2 пробела
 *   - STYLE-003: добавлены пробелы вокруг операторов
 */

#include "discrqa.h"
#include <float.h>
#include <math.h>

/**
 * @brief Трехточечный дискриминатор, аппроксимация квадратичной зависимостью.
 *
 * Аппроксимирует 3 точки параболой y = a*x² + b*x + c и находит вершину.
 *
 * Формулы:
 *   Ao = (A2 - A1) / (A2 - A3)
 *   xe = 0.5 * ((Ao-1)*x2² - Ao*x3² + x1²) / ((Ao-1)*x2 - Ao*x3 + x1)
 *
 * Граничные случаи:
 *   - A2 = A3: если A1 = A2 → x2; если A1 > A2 → x1; иначе → (x2+x3)/2
 *   - A1 = A2: если A3 > A2 → x3; иначе → (x1+x2)/2
 *
 * @param A1  амплитуда первой точки
 * @param A2  амплитуда второй точки
 * @param A3  амплитуда третьей точки
 * @param x1  координата первой точки
 * @param x2  координата второй точки
 * @param x3  координата третьей точки
 * @return    оценка координаты
 */
double discr3qa(double A1, double A2, double A3,
                double x1, double x2, double x3)
{
  if (fabs(A2 - A3) < DBL_EPSILON) {
    if (fabs(A2 - A1) < DBL_EPSILON)
      return x2;
    if (A1 > A2)
      return x1;
    else
      return 0.5 * (x3 + x2);
  }

  if (fabs(A2 - A1) < DBL_EPSILON) {
    if (A3 > A2)
      return x3;
    else
      return 0.5 * (x1 + x2);
  }

  {
    const double Ao = (A2 - A1) / (A2 - A3);
    double denom = (Ao - 1.0) * x2 - Ao * x3 + x1;

    if (fabs(denom) < DBL_EPSILON)
      return x2;

    return 0.5 * ((Ao - 1.0) * x2 * x2 - Ao * x3 * x3 + x1 * x1) / denom;
  }
}
