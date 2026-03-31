# HIP ↔ OpenCL Zero-Copy Proof of Concept

## Цель

Доказать, что память, выделенная через `hipMalloc()` (находится в VRAM GPU),
доступна для OpenCL kernels через `clSetKernelArgSVMPointer` **без копирования**.

## Что НЕ используется

| Технология | Статус |
|---|---|
| `clSVMAlloc` | ❌ Не используется |
| `cl_mem` / `clCreateBuffer` | ❌ Не используется |
| `CL_MEM_USE_HOST_PTR` | ❌ Не используется |
| `clEnqueueWriteBuffer` | ❌ Не используется |
| Копирование GPU→GPU | ❌ Не происходит |

## Что используется

| Технология | Назначение |
|---|---|
| `hipMalloc` | Выделение памяти в VRAM |
| `clSetKernelArgSVMPointer` | Передача VRAM-указателя в OpenCL kernel |
| HIP kernel launch (`<<<>>>`) | Чтение данных, записанных OpenCL |

## Алгоритм теста

```
1. hipMalloc → vec_a[10], vec_b[10], vec_c[10] в VRAM
2. hipMemset → обнуляем всё (доказываем что данные пишет именно OpenCL)
3. OpenCL kernel: vec_a[i] = (i+1)*10, vec_b[i] = (i+1)
4. HIP kernel: vec_c[i] = vec_a[i] + vec_b[i]
5. hipMemcpy → host, проверяем vec_c[i] == (i+1)*10 + (i+1)
```

## Сборка и запуск

```bash
# MI100
make GPU_ARCH=gfx908

# MI210/MI250
# make GPU_ARCH=gfx90a

# Запуск
make run
```

## Требования

- AMD MI100 (gfx908) или совместимый GPU
- ROCm 7.2+ с HIP и OpenCL runtime
- MLNX_OFED (для RDMA, опционально)

## Ожидаемый вывод

```
╔══════════════════════════════════════════════╗
║  HIP ↔ OpenCL Zero-Copy Proof of Concept    ║
║  hipMalloc → OpenCL writes → HIP reads+sums ║
╚══════════════════════════════════════════════╝

────────────────────────────────────────────────
ЭТАП 1: Инициализация HIP
────────────────────────────────────────────────
  GPU:  AMD Instinct MI100
  Arch: gfx908
  VRAM: 32768 MB

────────────────────────────────────────────────
ЭТАП 2: hipMalloc — 3 вектора в VRAM
────────────────────────────────────────────────
  d_vec_a = 0x7f1234560000  (VRAM)
  d_vec_b = 0x7f1234560100  (VRAM)
  d_vec_c = 0x7f1234560200  (VRAM)
  Все обнулены через hipMemset

  ...

  ┌───────┬────────────┬────────────┬────────────┬──────────┐
  │   i   │  vec_a[i]  │  vec_b[i]  │  vec_c[i]  │ expected │
  │       │ (OpenCL)   │ (OpenCL)   │ (HIP sum)  │  a+b     │
  ├───────┼────────────┼────────────┼────────────┼──────────┤
  │   0   │      10    │       1    │      11    │    11 ✓  │
  │   1   │      20    │       2    │      22    │    22 ✓  │
  │   2   │      30    │       3    │      33    │    33 ✓  │
  ...
  │   9   │     100    │      10    │     110    │   110 ✓  │
  └───────┴────────────┴────────────┴────────────┴──────────┘

  ══════════════════════════════════════════
  ✓ ТЕСТ ПРОЙДЕН: 10/10 элементов корректны
  ══════════════════════════════════════════

  ДОКАЗАНО: hipMalloc указатели работают в OpenCL
  kernels через clSetKernelArgSVMPointer.
  Один буфер в VRAM, два API, ноль копий.
```

## Почему это работает

На ROCm оба рантайма (HIP и OpenCL) построены поверх одного HSA runtime
(ROCR). `hipMalloc` возвращает указатель в едином виртуальном адресном
пространстве HSA. `clSetKernelArgSVMPointer` принимает любой валидный
указатель в этом пространстве — ему не важно, кто его выделил.

```
hipMalloc (HIP API)
    ↓
hsa_amd_memory_pool_allocate (HSA Runtime)
    ↓
VRAM физическая память (единая для обоих API)
    ↑
clSetKernelArgSVMPointer (OpenCL API)
```
