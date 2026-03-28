/****************************************************************************
*
*                             ОАО НПК НИИДАР
*                     107258, Москва, Бухвостова 11/12
*
*                    (c)Copyright 2009, НИИДАР, Москва
*
* Все права защищены.  Данная программа не предназначена для публикации  и
* копирования.  Программа состоит из конфиденциальных, содержащих
* коммерческую тайну НИИДАРа материалов. Любые попытки или участие
* в дешифрование, перепрограммировании и  ином изменении кода программы
* строго запрещены без письменного разрешения руководства НИИДАРа.
****************************************************************************/
/**
  @file    discrea.с
  @author  Добродумов А.Б.
  @date    15.04.2012
  @brief   Комплекс программ первичной обработки (КППО).
           Программа вычисления текущих замеров координат (ТЗК).
           Дискриминатор. Аппроксимация экспоненциальной зависимостью.
*/

#include <float.h>
#include <assert.h>
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include "../include/discrea.h"

static struct axstr
{
  double a;
  double x;
}ax[ 3 ];

static int compare( const void * p1, const void * p2 );
/**
  Трехточечный дискриминатор, аппрокимация экспоненциальной зависимостью.
  @param A1 – амплитуда первой точки.
  @param A2 – амплитуда второй точки.
  @param A3 – амплитуда третьей точки.
  @param x1 – координата первой точки.
  @param x2 – координата второй точки.
  @param x3 – координата третьей точки.
  @param xe – оценка координаты.
  @return 0 - успех.
*/
int discr3ea(double A1, double A2, double A3,
             double x1, double x2, double x3, double* xe)
{
  double a = 0, b = 0;
  double z1 = 0, z2 = 0, z3 = 0;
  double f1, f2, f3;
  double a1, a2, a3, a12, a23, a13;

  //-------------блок проверок входных параметров------------------//
  if (A1 < DBL_EPSILON || A2 < DBL_EPSILON || A3 < DBL_EPSILON) {
    *xe = x2;
    return EXIT_FAILURE;
  }

  if ( ( fabs( A1 - A2 ) < DBL_EPSILON) && ( fabs( A2 - A3 ) < DBL_EPSILON) ) {
    *xe = x2;
    return EXIT_FAILURE;
  }

  ax[ 0 ].a = A1; ax[ 0 ].x = x1;
  ax[ 1 ].a = A2; ax[ 1 ].x = x2;
  ax[ 2 ].a = A3; ax[ 2 ].x = x3;

  // сортировка по координате, координата должна возрастать
  qsort( ax, 3, sizeof( struct axstr ), compare );
  a1 = ax[ 0 ].a; a2 = ax[ 1 ].a; a3 = ax[ 2 ].a;
  f1 = ax[ 0 ].x; f2 = ax[ 1 ].x; f3 = ax[ 2 ].x;

  // проверка на вогнутость, если да, то возвращаем максимум
  a12 = a1 - a2;
  a23 = a2 - a3;
  a13 = a1 - a3;
  if ( (a12 < 0 && a23 < 0 && a12 > a23) || // например 2 4 8
       (a12 > 0 && a23 < 0 && a13 < 0) )    // например 6 4 8
  {
    *xe = x3;
    return EXIT_FAILURE; // или же переход на 2-х точечный дискриминатор
  }
  if ( (a12 > 0 && a23 > 0 && a12 > a23) || // например 8 4 2
       (a12 > 0 && a23 < 0 && a13 > 0) )    // например 8 4 6
  {
    *xe = x1;
    return EXIT_FAILURE; // или же переход на 2-х точечный дискриминатор
  }
  //f2 = 2*((a(2)-a(1))/(x(2)-x(1)) - (a(3)-a(2))/(x(3)-x(2)))/(x(1)-x(3)) - оценка знака второй производной
  //--------------------------------------------------------------//

  z1 = log(a1);
  z2 = log(a2);
  z3 = log(a3);

  a = z1*(f2*f2 - f3*f3) + z2*(f3*f3 - f1*f1) + z3*(f1*f1 - f2*f2);
  b = z1*(f2 - f3) + z2*(f3 - f1) + z3*(f1 - f2);

  if(fabs(b) < DBL_EPSILON) //если b=0
  {
    if(a*b>=0) {
      *xe = f3+0.5*(f3-f1);
      return EXIT_FAILURE;
    }
    else {
      *xe = f1-0.5*(f3-f1);
      return EXIT_FAILURE;
    }
  }

  *xe = 0.5*a/b;
  
  if (*xe > f3+0.5*(f3-f1)) {
    *xe = f3+0.5*(f3-f1); //ограничение на вылет оценки за пределы зондирования
    return EXIT_FAILURE;
  }
  if (*xe < f1-0.5*(f3-f1)) {
    *xe = f1-0.5*(f3-f1); //ограничение на вылет оценки за пределы зондирования
    return EXIT_FAILURE;
  }

  return EXIT_SUCCESS;
}

/**
  Трехточечный дискриминатор, аппрокимация экспоненциальной зависимостью.
  
  Уточнение амплитуды.

  @param A1 – амплитуда первой точки.
  @param A2 – амплитуда второй точки.
  @param A3 – амплитуда третьей точки.
  @param x1 – координата первой точки.
  @param x2 – координата второй точки.
  @param xe – вычисленное уточненное значение координаты, xe = discr3ea(a1, a2, a3, x1, x2, x3).

  @return уточненное значение амплитуды.
*/
double discr3eaY(double A1, double A2, double x1, double x2, double xe)
{
  double ye = A2, yMax;
  double z1, z2;
  double a0, dxe;

  if ( A1 < DBL_EPSILON || A2 < DBL_EPSILON)
    return 0.0;

  yMax = ( A1 > A2 ) ? A1 : A2;
  
  z1 = log(A1);
  z2 = log(A2);
  
  a0 = (2 * xe * (x1 - x2) - x1 * x1 + x2 * x2);
  
  if ( fabs(a0) < DBL_EPSILON)
    return yMax;

  a0 = (z1 - z2) / a0;
  
  dxe = x2 - xe;
  ye = A2 * exp( a0 * dxe * dxe );
  
  return ye;
}

static int compare( const void * p1, const void * p2 )
{
  struct axstr *ax1 = ( struct axstr* ) p1;
  struct axstr *ax2 = ( struct axstr* ) p2;

  if ( ax1->x < ax2->x )
    return -1;
  else if ( ax1->x > ax2->x )
    return 1;

  return 0;
}