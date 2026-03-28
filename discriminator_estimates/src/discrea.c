/**
 * @file    discrea.c
 * @author  Добродумов А.Б.
 * @date    15.04.2012
 * @brief   КППО / ТЗК. Дискриминатор — экспоненциальная аппроксимация (Exponential).
 *
 * Аппроксимация отсчётов ДН функцией y = A_max * exp(-a*(x - x0)²)
 * для нахождения координаты максимума x0.
 *
 * Рефакторинг: Кодо, 2026-03-28
 * Изменения:
 *   - ERR-002: static ax[3] перенесена в локальную переменную (thread-safety)
 *   - STYLE: единые 2-пробельные отступы
 */

#include <float.h>
#include <math.h>
#include <stdlib.h>
#include "discrea.h"

/** @brief Структура для сортировки пар (амплитуда, координата). */
typedef struct {
  double a;  /**< амплитуда */
  double x;  /**< координата */
} axstr_t;

static int compare_by_x(const void *p1, const void *p2);

/**
 * @brief Трехточечный дискриминатор, экспоненциальная аппроксимация.
 *
 * Алгоритм:
 *   1. Проверка входных данных (ненулевые амплитуды, не все равны)
 *   2. Сортировка по координате (x должна возрастать)
 *   3. Проверка на выпуклость (максимум должен быть в центре)
 *   4. Логарифмирование: z = ln(A), аппроксимация параболой z(x)
 *   5. Вершина параболы: xe = 0.5 * a / b
 *   6. Ограничение на вылет за пределы зондирования
 *
 * @param A1  амплитуда первой точки (должна быть > 0)
 * @param A2  амплитуда второй точки (должна быть > 0)
 * @param A3  амплитуда третьей точки (должна быть > 0)
 * @param x1  координата первой точки
 * @param x2  координата второй точки
 * @param x3  координата третьей точки
 * @param xe  [out] оценка координаты
 * @return    EXIT_SUCCESS (0) при успехе, EXIT_FAILURE (1) при ошибке
 *            (при ошибке *xe содержит приближённое значение)
 */
int discr3ea(double A1, double A2, double A3,
             double x1, double x2, double x3, double *xe)
{
  double a = 0.0, b = 0.0;
  double z1, z2, z3;
  double f1, f2, f3;
  double a1, a2, a3, a12, a23, a13;
  /* ERR-002 fix: локальная переменная вместо static */
  axstr_t ax[3];

  /* Проверка: все амплитуды должны быть положительны */
  if (A1 < DBL_EPSILON || A2 < DBL_EPSILON || A3 < DBL_EPSILON) {
    *xe = x2;
    return EXIT_FAILURE;
  }

  /* Проверка: не все амплитуды равны */
  if ((fabs(A1 - A2) < DBL_EPSILON) && (fabs(A2 - A3) < DBL_EPSILON)) {
    *xe = x2;
    return EXIT_FAILURE;
  }

  /* Сортировка по координате (x должна возрастать) */
  ax[0].a = A1; ax[0].x = x1;
  ax[1].a = A2; ax[1].x = x2;
  ax[2].a = A3; ax[2].x = x3;
  qsort(ax, 3, sizeof(axstr_t), compare_by_x);

  a1 = ax[0].a; a2 = ax[1].a; a3 = ax[2].a;
  f1 = ax[0].x; f2 = ax[1].x; f3 = ax[2].x;

  /* Проверка на выпуклость: максимум должен быть в центре */
  a12 = a1 - a2;
  a23 = a2 - a3;
  a13 = a1 - a3;

  /* Вогнутость: максимум справа (например 2, 4, 8) */
  if ((a12 < 0 && a23 < 0 && a12 > a23) ||
      (a12 > 0 && a23 < 0 && a13 < 0)) {
    *xe = x3;
    return EXIT_FAILURE;
  }
  /* Вогнутость: максимум слева (например 8, 4, 2) */
  if ((a12 > 0 && a23 > 0 && a12 > a23) ||
      (a12 > 0 && a23 < 0 && a13 > 0)) {
    *xe = x1;
    return EXIT_FAILURE;
  }

  /* Логарифмирование */
  z1 = log(a1);
  z2 = log(a2);
  z3 = log(a3);

  /* Коэффициенты параболы z(x) = a + b*x + ... */
  a = z1 * (f2 * f2 - f3 * f3) + z2 * (f3 * f3 - f1 * f1) + z3 * (f1 * f1 - f2 * f2);
  b = z1 * (f2 - f3) + z2 * (f3 - f1) + z3 * (f1 - f2);

  if (fabs(b) < DBL_EPSILON) {
    if (a * b >= 0) {
      *xe = f3 + 0.5 * (f3 - f1);
      return EXIT_FAILURE;
    } else {
      *xe = f1 - 0.5 * (f3 - f1);
      return EXIT_FAILURE;
    }
  }

  /* Вершина параболы */
  *xe = 0.5 * a / b;

  /* Ограничение на вылет за пределы зондирования */
  if (*xe > f3 + 0.5 * (f3 - f1)) {
    *xe = f3 + 0.5 * (f3 - f1);
    return EXIT_FAILURE;
  }
  if (*xe < f1 - 0.5 * (f3 - f1)) {
    *xe = f1 - 0.5 * (f3 - f1);
    return EXIT_FAILURE;
  }

  return EXIT_SUCCESS;
}

/**
 * @brief Уточнение амплитуды по экспоненциальной аппроксимации.
 *
 * Формула: ye = A2 * exp(a0 * (x2 - xe)²)
 *
 * @param A1  амплитуда первой точки
 * @param A2  амплитуда второй точки
 * @param x1  координата первой точки
 * @param x2  координата второй точки
 * @param xe  вычисленная координата (результат discr3ea)
 * @return    уточнённое значение амплитуды
 */
double discr3eaY(double A1, double A2, double x1, double x2, double xe)
{
  double ye, yMax;
  double z1, z2;
  double a0, dxe;

  if (A1 < DBL_EPSILON || A2 < DBL_EPSILON)
    return 0.0;

  yMax = (A1 > A2) ? A1 : A2;

  z1 = log(A1);
  z2 = log(A2);

  a0 = (2.0 * xe * (x1 - x2) - x1 * x1 + x2 * x2);

  if (fabs(a0) < DBL_EPSILON)
    return yMax;

  a0 = (z1 - z2) / a0;

  dxe = x2 - xe;
  ye = A2 * exp(a0 * dxe * dxe);

  return ye;
}

/**
 * @brief Сортировка пар (амплитуда, координата) по возрастанию координаты.
 */
static int compare_by_x(const void *p1, const void *p2)
{
  const axstr_t *ax1 = (const axstr_t *)p1;
  const axstr_t *ax2 = (const axstr_t *)p2;

  if (ax1->x < ax2->x)
    return -1;
  else if (ax1->x > ax2->x)
    return 1;
  return 0;
}
