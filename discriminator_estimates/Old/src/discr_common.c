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
@file    discr_common.c
@author  Керский Е.В.
@date    06.07.2017
@brief   Комплекс программ первичной обработки (КППО).
Программа вычисления текущих замеров координат (ТЗК).
Обертки для дискриминаторных оценок.
*/

#ifndef _USE_MATH_DEFINES
#define _USE_MATH_DEFINES
#endif
#include <stdio.h>
#include <math.h>
#include <float.h>

#include "../include/discr_common.h"
#include "../include/discrea.h"
#include "../include/discrqa.h"

/**
@param maz  – [in] массив азимутальных координат.
@param mel  – [in] массив угломестных координат.
@param mval – [in] массив амплитуд.
@param ndnx – [in] кол-во ДН по оси Х.
@param ndny – [in] кол-во ДН по оси У.
@param az  – [out] уточненная координата азимута.
@param el  – [out] уточненная координата угла места.
@param val – [out] уточненная значение амплитуды.
@return -1 ошибка проведения оценки, 0 - норма.
*/
//<! Трехточечный дискриминатор.
int discr3( double **maz, double **mel, double **mval, int ndnx, int ndny, 
            DISCRTYPE discrtype, double dx, double lambda,
            double *az, double *el, double *val )
{
  double aztmp = 0.0, eltmp = 0.0, valaz = 0.0, valel = 0.0;
  int maxRow = 0, maxCol = 0;
  double maxAmpl = -1;
  const double c = 2.0 * M_PI * dx / lambda;
  int i, j;

  // проверка на возможность использования 3-х точечного дискриминатора, причины по которым такой дискриминатора использовать нельзя:
  // отсутствие максимума в центре, наличине вогнутости, координата аз, ум убывает ...
  // это может сильно исказить оценку, в таком случае нужно переходить на оценку 2-х точечным дискриминатором
  if ( !checkuse3d( maz, mel, mval, ndnx, ndny ) )
    return -1;
  
  for ( i = 0; i < ndnx; ++i )
  for ( j = 0; j < ndny; ++j )
  {
    if ( mval[ i ][ j ] > maxAmpl )
    {
      maxRow = i;
      maxCol = j;
      maxAmpl = mval[ i ][ j ];
    }
  } // нашли строку и столбец с максимальной амплитудой

  // умножаем координаты на коэффициент
  for ( i = 0; i < ndnx; ++i )
  for ( j = 0; j < ndny; ++j )
  {
    maz[ i ][ j ] *= c;
    mel[ i ][ j ] *= c;
  }
   
  switch ( discrtype )
  {
    case DT_QA:
      aztmp = discr3qa( mval[ maxRow ][ 0 ], mval[ maxRow ][ 1 ], mval[ maxRow ][ 2 ],
                        maz[ maxRow ][ 0 ], maz[ maxRow ][ 1 ], maz[ maxRow ][ 2 ] );
      eltmp = discr3qa( mval[ 0 ][ maxCol ], mval[ 1 ][ maxCol ], mval[ 2 ][ maxCol ],
                        mel[ 0 ][ maxCol ], mel[ 1 ][ maxCol ], mel[ 2 ][ maxCol ] );
      *val = maxAmpl;
      break;
    case DT_EA:
      discr3ea( mval[ maxRow ][ 0 ], mval[ maxRow ][ 1 ], mval[ maxRow ][ 2 ],
                maz[ maxRow ][ 0 ], maz[ maxRow ][ 1 ], maz[ maxRow ][ 2 ], &aztmp);
      discr3ea( mval[ 0 ][ maxCol ], mval[ 1 ][ maxCol ], mval[ 2 ][ maxCol ],
                mel[ 0 ][ maxCol ], mel[ 1 ][ maxCol ], mel[ 2 ][ maxCol ], &eltmp);

      valaz = discr3eaY( mval[ maxRow ][ 0 ], mval[ maxRow ][ 1 ],
                         maz[ maxRow ][ 0 ], maz[ maxRow ][ 1 ], aztmp );
      valel = discr3eaY( mval[ 0 ][ maxCol ], mval[ 1 ][ maxCol ],
                         mel[ 0 ][ maxCol ], mel[ 1 ][ maxCol ], eltmp );

      *val = ( valaz > valel ) ? valaz : valel;
      *val = ( maxAmpl > *val ) ? maxAmpl : *val;
      break;
    default: *az = 0.0; *el = 0.0; *val = 0.0;
      return -2;
  }

  *az = aztmp / c;
  *el = eltmp / c;
  
  return 0;
}

/**
@param maz  – [in] массив азимутальных координат.
@param mel  – [in] массив угломестных координат.
@param mval – [in] массив амплитуд.
@return 1 - да, 0 - нет.
*/
//<! проверка на возможность использования 3-х точечного дискриминатора.
int checkuse3d( double **maz, double **mel, double **mval, int ndnx, int ndny )
{
  int i, j;
  (void)maz;
  (void)mel;

  for ( i = 0; i < ndnx; i++ )
  for ( j = 0; j < ndny; j++ )
  {
    if ( mval[ i ][ j ] < FLT_EPSILON )
      return 0;
  }
  return 1;
}

/**
@param maz  – [in] массив азимутальных координат.
@param mel  – [in] массив угломестных координат.
@param mval – [in] массив амплитуд.
@param az  – [out] уточненная координата азимута.
@param el  – [out] уточненная координата угла места.
@param val – [out] уточненная значение амплитуды.
@return -1 ошибка проведения оценки, 0 - норма.
*/
//<! Трехточечный дискриминатор.
int discr3_( double maz[ 3 ][ 3 ], double mel[ 3 ][ 3 ], double mval[ 3 ][ 3 ],
             DISCRTYPE discrtype, double dx, double lambda,
             double *az, double *el, double *val )
{
  double *pmaz[ 3 ] = { &maz[ 0 ][ 0 ], &maz[ 1 ][ 0 ], &maz[ 2 ][ 0 ] };
  double *pmel[ 3 ] = { &mel[ 0 ][ 0 ], &mel[ 1 ][ 0 ], &mel[ 2 ][ 0 ] };
  double *pmval[ 3 ] = { &mval[ 0 ][ 0 ], &mval[ 1 ][ 0 ], &mval[ 2 ][ 0 ] };

  int res = discr3( pmaz, pmel, pmval, 3, 3,
                    discrtype, dx, lambda,
                    az, el, val );

  return res;
}
