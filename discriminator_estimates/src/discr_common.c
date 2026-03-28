/**
 * @file    discr_common.c
 * @author  Керский Е.В.
 * @date    06.07.2017
 * @brief   КППО / ТЗК. Обёртки для дискриминаторных оценок.
 *
 * Рефакторинг: Кодо, 2026-03-28
 * Изменения:
 *   - ERR-001: реализованы discr2() и conv3to2()
 *   - ERR-003: discr3() больше НЕ модифицирует входные maz/mel (работает с копиями)
 *   - ERR-004: FLT_EPSILON → DBL_EPSILON
 *   - ERR-006: добавлена поддержка DT_CG в discr3()
 *   - STYLE: единые 2-пробельные отступы
 */

#ifndef _USE_MATH_DEFINES
#define _USE_MATH_DEFINES
#endif
#include <stdio.h>
#include <math.h>
#include <float.h>

#include "discr_common.h"
#include "discrcg.h"
#include "discrea.h"
#include "discrqa.h"

/**
 * @brief Двухточечный дискриминатор (обёртка), центр тяжести.
 *
 * Принимает матрицы 2x2 координат и амплитуд ДН.
 * Находит строку/столбец с максимумом и оценивает az, el
 * через discr2cg().
 *
 * @param maz   [in] массив азимутальных координат 2x2
 * @param mel   [in] массив угломестных координат 2x2
 * @param mval  [in] массив амплитуд 2x2
 * @param az    [out] уточнённая координата азимута
 * @param el    [out] уточнённая координата угла места
 * @param val   [out] уточнённое значение амплитуды
 * @return      0 — норма, -1 — ошибка
 */
int discr2(double maz[2][2], double mel[2][2], double mval[2][2],
           double *az, double *el, double *val)
{
  int maxRow = 0, maxCol = 0;
  double maxAmpl = -1.0;
  int i, j;

  /* Проверка: все амплитуды должны быть положительны */
  for (i = 0; i < 2; ++i)
    for (j = 0; j < 2; ++j)
      if (mval[i][j] < DBL_EPSILON) {
        *az = 0.0; *el = 0.0; *val = 0.0;
        return -1;
      }

  /* Поиск максимума */
  for (i = 0; i < 2; ++i)
    for (j = 0; j < 2; ++j)
      if (mval[i][j] > maxAmpl) {
        maxRow = i;
        maxCol = j;
        maxAmpl = mval[i][j];
      }

  /* Оценка по азимуту (по строке maxRow) */
  *az = discr2cg(mval[maxRow][0], mval[maxRow][1],
                 maz[maxRow][0],  maz[maxRow][1]);

  /* Оценка по углу места (по столбцу maxCol) */
  *el = discr2cg(mval[0][maxCol], mval[1][maxCol],
                 mel[0][maxCol],  mel[1][maxCol]);

  *val = maxAmpl;
  return 0;
}

/**
 * @brief Трехточечный дискриминатор (обёртка).
 *
 * Принимает матрицы ndnx x ndny координат и амплитуд ДН.
 * Поддерживает типы: DT_CG, DT_QA, DT_EA.
 *
 * @warning Функция НЕ модифицирует входные массивы maz, mel
 *          (исправлено в рефакторинге, ERR-003).
 *
 * @param maz       [in] массив азимутальных координат
 * @param mel       [in] массив угломестных координат
 * @param mval      [in] массив амплитуд
 * @param ndnx      [in] число ДН по оси X
 * @param ndny      [in] число ДН по оси Y
 * @param discrtype [in] тип дискриминатора (DT_CG, DT_QA, DT_EA)
 * @param dx        [in] шаг по углу (используется для DT_QA, DT_EA)
 * @param lambda    [in] длина волны (используется для DT_QA, DT_EA)
 * @param az        [out] уточнённая координата азимута
 * @param el        [out] уточнённая координата угла места
 * @param val       [out] уточнённое значение амплитуды
 * @return          0 — норма, -1 — нельзя использовать 3-точ., -2 — неизвестный тип
 */
int discr3(double **maz, double **mel, double **mval, int ndnx, int ndny,
           DISCRTYPE discrtype, double dx, double lambda,
           double *az, double *el, double *val)
{
  double aztmp = 0.0, eltmp = 0.0, valaz = 0.0, valel = 0.0;
  int maxRow = 0, maxCol = 0;
  double maxAmpl = -1.0;
  const double c = 2.0 * M_PI * dx / lambda;
  int i, j;

  /* Проверка на возможность использования 3-точечного дискриминатора */
  if (!checkuse3d(maz, mel, mval, ndnx, ndny))
    return -1;

  /* Поиск строки и столбца с максимальной амплитудой */
  for (i = 0; i < ndnx; ++i)
    for (j = 0; j < ndny; ++j)
      if (mval[i][j] > maxAmpl) {
        maxRow = i;
        maxCol = j;
        maxAmpl = mval[i][j];
      }

  switch (discrtype) {
    case DT_CG:
      /* ERR-006 fix: добавлена поддержка центра тяжести */
      if (ndny >= 3) {
        aztmp = discr3cg(mval[maxRow][0], mval[maxRow][1], mval[maxRow][2],
                         maz[maxRow][0],  maz[maxRow][1],  maz[maxRow][2]);
      }
      if (ndnx >= 3) {
        eltmp = discr3cg(mval[0][maxCol], mval[1][maxCol], mval[2][maxCol],
                         mel[0][maxCol],  mel[1][maxCol],  mel[2][maxCol]);
      }
      *val = maxAmpl;
      break;

    case DT_QA:
      /* ERR-003 fix: координаты умножаем на c локально, не модифицируя входные данные */
      aztmp = discr3qa(mval[maxRow][0], mval[maxRow][1], mval[maxRow][2],
                       maz[maxRow][0] * c, maz[maxRow][1] * c, maz[maxRow][2] * c);
      eltmp = discr3qa(mval[0][maxCol], mval[1][maxCol], mval[2][maxCol],
                       mel[0][maxCol] * c, mel[1][maxCol] * c, mel[2][maxCol] * c);
      *val = maxAmpl;
      /* Обратное преобразование из масштабированных координат */
      *az = aztmp / c;
      *el = eltmp / c;
      return 0;

    case DT_EA:
      /* ERR-003 fix: координаты умножаем на c локально */
      discr3ea(mval[maxRow][0], mval[maxRow][1], mval[maxRow][2],
               maz[maxRow][0] * c, maz[maxRow][1] * c, maz[maxRow][2] * c, &aztmp);
      discr3ea(mval[0][maxCol], mval[1][maxCol], mval[2][maxCol],
               mel[0][maxCol] * c, mel[1][maxCol] * c, mel[2][maxCol] * c, &eltmp);

      valaz = discr3eaY(mval[maxRow][0], mval[maxRow][1],
                        maz[maxRow][0] * c, maz[maxRow][1] * c, aztmp);
      valel = discr3eaY(mval[0][maxCol], mval[1][maxCol],
                        mel[0][maxCol] * c, mel[1][maxCol] * c, eltmp);

      *val = (valaz > valel) ? valaz : valel;
      *val = (maxAmpl > *val) ? maxAmpl : *val;
      /* Обратное преобразование */
      *az = aztmp / c;
      *el = eltmp / c;
      return 0;

    default:
      *az = 0.0; *el = 0.0; *val = 0.0;
      return -2;
  }

  /* Для DT_CG — координаты не масштабируются */
  *az = aztmp;
  *el = eltmp;
  return 0;
}

/**
 * @brief Проверка на возможность использования 3-точечного дискриминатора.
 *
 * Проверяет что все амплитуды положительны.
 *
 * @param maz   [in] массив азимутальных координат (не используется, для совместимости)
 * @param mel   [in] массив угломестных координат (не используется, для совместимости)
 * @param mval  [in] массив амплитуд
 * @param ndnx  [in] число ДН по оси X
 * @param ndny  [in] число ДН по оси Y
 * @return      1 — можно использовать, 0 — нельзя
 */
int checkuse3d(double **maz, double **mel, double **mval, int ndnx, int ndny)
{
  int i, j;
  (void)maz;
  (void)mel;

  for (i = 0; i < ndnx; i++)
    for (j = 0; j < ndny; j++)
      if (mval[i][j] < DBL_EPSILON)  /* ERR-004 fix: was FLT_EPSILON */
        return 0;
  return 1;
}

/**
 * @brief Адаптер discr3 для статических массивов 3x3.
 *
 * Преобразует массивы double[3][3] в double** для вызова discr3().
 *
 * @param maz       [in] массив азимутальных координат 3x3
 * @param mel       [in] массив угломестных координат 3x3
 * @param mval      [in] массив амплитуд 3x3
 * @param discrtype [in] тип дискриминатора
 * @param dx        [in] шаг по углу
 * @param lambda    [in] длина волны
 * @param az        [out] уточнённая координата азимута
 * @param el        [out] уточнённая координата угла места
 * @param val       [out] уточнённое значение амплитуды
 * @return          0 — норма, -1 — ошибка, -2 — неизвестный тип
 */
int discr3_(double maz[3][3], double mel[3][3], double mval[3][3],
            DISCRTYPE discrtype, double dx, double lambda,
            double *az, double *el, double *val)
{
  double *pmaz[3]  = { &maz[0][0],  &maz[1][0],  &maz[2][0] };
  double *pmel[3]  = { &mel[0][0],  &mel[1][0],  &mel[2][0] };
  double *pmval[3] = { &mval[0][0], &mval[1][0], &mval[2][0] };

  return discr3(pmaz, pmel, pmval, 3, 3,
                discrtype, dx, lambda,
                az, el, val);
}

/**
 * @brief Выделение подматрицы 2x2 из 3x3 для перехода на 2-точечный дискриминатор.
 *
 * Выбирает квадрант 2x2 с максимальной суммарной амплитудой.
 * Используется когда 3-точечный дискриминатор невозможен
 * (checkuse3d вернул 0, вогнутость и т.д.).
 *
 * @param maz3   [in]  азимутальные координаты 3x3
 * @param mel3   [in]  угломестные координаты 3x3
 * @param mval3  [in]  амплитуды 3x3
 * @param maz2   [out] азимутальные координаты 2x2
 * @param mel2   [out] угломестные координаты 2x2
 * @param mval2  [out] амплитуды 2x2
 * @return       0 — успех
 */
int conv3to2(double maz3[3][3], double mel3[3][3], double mval3[3][3],
             double maz2[2][2], double mel2[2][2], double mval2[2][2])
{
  int bestR = 0, bestC = 0;
  double bestSum = -1.0;
  int r, c, i, j;

  /* Перебираем все 4 квадранта 2x2 (смещения: (0,0), (0,1), (1,0), (1,1)) */
  for (r = 0; r < 2; r++) {
    for (c = 0; c < 2; c++) {
      double sum = mval3[r][c]     + mval3[r][c + 1]
                 + mval3[r + 1][c] + mval3[r + 1][c + 1];
      if (sum > bestSum) {
        bestSum = sum;
        bestR = r;
        bestC = c;
      }
    }
  }

  /* Копируем выбранный квадрант */
  for (i = 0; i < 2; i++) {
    for (j = 0; j < 2; j++) {
      maz2[i][j]  = maz3[bestR + i][bestC + j];
      mel2[i][j]  = mel3[bestR + i][bestC + j];
      mval2[i][j] = mval3[bestR + i][bestC + j];
    }
  }

  return 0;
}
