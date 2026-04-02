Тесты
=====

Запуск
------

.. code-block:: bash

   # Основные тесты дискриминаторов
   python test_python/test_discriminators.py

   # Визуализация ошибок (3 графика)
   python test_python/test_discriminators_plot.py

   # Тесты signal_gen
   python test_python/test_signal_gen.py

Таблица точности
----------------

Sweep ±df/4, N=32, окно Hamming:

======= =============== =============
Метод   Средняя ошибка  Макс. ошибка
======= =============== =============
EXP     2 902 Hz        4 825 Hz
SQR     13 553 Hz       23 348 Hz
LAY     22 933 Hz       43 811 Hz
CG      84 664 Hz       115 270 Hz
SD      138 393 Hz      187 500 Hz
======= =============== =============
