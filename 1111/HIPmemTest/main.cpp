// ============================================================
// PROOF OF CONCEPT: hipMalloc → OpenCL writes → HIP sums
// Radeon 9070 (gfx1201), ROCm 7.2+, Linux — как GPUWorkLib
//
// Доказываем: память, выделенная через hipMalloc (VRAM),
// доступна для OpenCL kernels через clSetKernelArgSVMPointer,
// и результаты видны в HIP kernels БЕЗ КОПИРОВАНИЯ.
//
// Шаги:
//   1) hipMalloc: vec_a[10], vec_b[10], vec_c[10] — всё в VRAM
//   2) OpenCL kernel: заполняет vec_a и vec_b значениями
//   3) HIP kernel: vec_c[i] = vec_a[i] + vec_b[i]
//   4) hipMemcpy vec_c → host, проверяем результат
//   5) Для отчёта: выводим адреса, значения, подтверждение
// ============================================================

#include <hip/hip_runtime.h>
#include <CL/cl.h>
#include <cstdio>
#include <cstdlib>
#include <cstring>

#define VEC_SIZE 10

// ============================================================
// HIP KERNEL: суммируем vec_a + vec_b → vec_c
// Читает данные, которые записал OpenCL kernel.
// Если zero-copy работает — значения будут корректны.
// ============================================================
__global__ void hip_vector_add(const int* a, const int* b, int* c, int n) {
    int i = blockIdx.x * blockDim.x + threadIdx.x;
    if (i < n) {
        c[i] = a[i] + b[i];
    }
}

// ============================================================
// Утилиты
// ============================================================
#define HIP_CHECK(call)                                              \
    do {                                                             \
        hipError_t err = (call);                                     \
        if (err != hipSuccess) {                                     \
            fprintf(stderr, "HIP ERROR [%s:%d]: %s → %s\n",         \
                    __FILE__, __LINE__, #call,                       \
                    hipGetErrorString(err));                          \
            exit(1);                                                 \
        }                                                            \
    } while (0)

#define CL_CHECK(call)                                               \
    do {                                                             \
        cl_int err = (call);                                         \
        if (err != CL_SUCCESS) {                                     \
            fprintf(stderr, "OpenCL ERROR [%s:%d]: %s → code %d\n", \
                    __FILE__, __LINE__, #call, err);                  \
            exit(1);                                                 \
        }                                                            \
    } while (0)

void print_separator() {
    printf("────────────────────────────────────────────────\n");
}

// ============================================================
// OpenCL kernel: заполняет vec_a = {10,20,...,100}
//                         vec_b = {1,2,...,10}
//
// Сигнатура: __global int* — стандартная, ничего необычного.
// Ядро НЕ знает что указатель пришёл из hipMalloc.
// ============================================================
const char* ocl_kernel_source = R"CLC(
__kernel void fill_vectors(__global int* a,
                           __global int* b,
                           int n)
{
    int i = get_global_id(0);
    if (i < n) {
        a[i] = (i + 1) * 10;   // 10, 20, 30, ..., 100
        b[i] = (i + 1);        //  1,  2,  3, ...,  10
    }
}
)CLC";

int main() {
    printf("\n");
    printf("╔══════════════════════════════════════════════╗\n");
    printf("║  HIP ↔ OpenCL Zero-Copy Proof of Concept    ║\n");
    printf("║  hipMalloc → OpenCL writes → HIP reads+sums ║\n");
    printf("╚══════════════════════════════════════════════╝\n\n");

    // ========================================================
    // ЭТАП 1: Инициализация HIP
    // ========================================================
    print_separator();
    printf("ЭТАП 1: Инициализация HIP\n");
    print_separator();

    HIP_CHECK(hipSetDevice(0));

    hipDeviceProp_t props;
    HIP_CHECK(hipGetDeviceProperties(&props, 0));
    printf("  GPU:  %s\n", props.name);
    printf("  Arch: %s\n", props.gcnArchName);
    printf("  VRAM: %zu MB\n", props.totalGlobalMem / (1024 * 1024));

    // ========================================================
    // ЭТАП 2: Выделяем 3 вектора через hipMalloc (VRAM!)
    // ========================================================
    print_separator();
    printf("ЭТАП 2: hipMalloc — 3 вектора в VRAM\n");
    print_separator();

    int* d_vec_a = nullptr;
    int* d_vec_b = nullptr;
    int* d_vec_c = nullptr;

    HIP_CHECK(hipMalloc(&d_vec_a, VEC_SIZE * sizeof(int)));
    HIP_CHECK(hipMalloc(&d_vec_b, VEC_SIZE * sizeof(int)));
    HIP_CHECK(hipMalloc(&d_vec_c, VEC_SIZE * sizeof(int)));

    // Обнуляем всё — чтобы доказать что OpenCL действительно пишет
    HIP_CHECK(hipMemset(d_vec_a, 0, VEC_SIZE * sizeof(int)));
    HIP_CHECK(hipMemset(d_vec_b, 0, VEC_SIZE * sizeof(int)));
    HIP_CHECK(hipMemset(d_vec_c, 0, VEC_SIZE * sizeof(int)));

    printf("  d_vec_a = %p  (VRAM)\n", (void*)d_vec_a);
    printf("  d_vec_b = %p  (VRAM)\n", (void*)d_vec_b);
    printf("  d_vec_c = %p  (VRAM)\n", (void*)d_vec_c);
    printf("  Все обнулены через hipMemset\n");

    // ========================================================
    // ЭТАП 3: Инициализация OpenCL + проверка SVM
    // ========================================================
    print_separator();
    printf("ЭТАП 3: Инициализация OpenCL\n");
    print_separator();

    cl_int cl_err;
    cl_platform_id platform;
    cl_device_id   cl_dev;

    CL_CHECK(clGetPlatformIDs(1, &platform, nullptr));
    CL_CHECK(clGetDeviceIDs(platform, CL_DEVICE_TYPE_GPU, 1, &cl_dev, nullptr));

    // Имя устройства
    char dev_name[256] = {};
    clGetDeviceInfo(cl_dev, CL_DEVICE_NAME, sizeof(dev_name), dev_name, nullptr);
    printf("  OpenCL device: %s\n", dev_name);

    // Версия OpenCL
    char dev_ver[256] = {};
    clGetDeviceInfo(cl_dev, CL_DEVICE_VERSION, sizeof(dev_ver), dev_ver, nullptr);
    printf("  OpenCL version: %s\n", dev_ver);

    // Проверяем SVM capabilities
    cl_device_svm_capabilities svm_caps = 0;
    clGetDeviceInfo(cl_dev, CL_DEVICE_SVM_CAPABILITIES,
                    sizeof(svm_caps), &svm_caps, nullptr);

    printf("  SVM coarse grain: %s\n",
           (svm_caps & CL_DEVICE_SVM_COARSE_GRAIN_BUFFER) ? "YES ✓" : "NO ✗");
    printf("  SVM fine grain:   %s\n",
           (svm_caps & CL_DEVICE_SVM_FINE_GRAIN_BUFFER) ? "YES ✓" : "NO ✗");
    printf("  SVM atomics:      %s\n",
           (svm_caps & CL_DEVICE_SVM_ATOMICS) ? "YES ✓" : "NO ✗");

    if (!(svm_caps & CL_DEVICE_SVM_COARSE_GRAIN_BUFFER)) {
        fprintf(stderr, "\n  FATAL: SVM не поддерживается на этом устройстве!\n");
        return 1;
    }

    cl_context cl_ctx = clCreateContext(nullptr, 1, &cl_dev,
                                         nullptr, nullptr, &cl_err);
    CL_CHECK(cl_err);

    cl_command_queue cl_queue = clCreateCommandQueueWithProperties(
        cl_ctx, cl_dev, nullptr, &cl_err);
    CL_CHECK(cl_err);

    // ========================================================
    // ЭТАП 4: Компилируем OpenCL kernel
    // ========================================================
    print_separator();
    printf("ЭТАП 4: Компиляция OpenCL kernel\n");
    print_separator();

    cl_program prog = clCreateProgramWithSource(
        cl_ctx, 1, &ocl_kernel_source, nullptr, &cl_err);
    CL_CHECK(cl_err);

    cl_err = clBuildProgram(prog, 1, &cl_dev, nullptr, nullptr, nullptr);
    if (cl_err != CL_SUCCESS) {
        char log[4096] = {};
        clGetProgramBuildInfo(prog, cl_dev, CL_PROGRAM_BUILD_LOG,
                              sizeof(log), log, nullptr);
        fprintf(stderr, "  Build log:\n%s\n", log);
        return 1;
    }

    cl_kernel ocl_kernel = clCreateKernel(prog, "fill_vectors", &cl_err);
    CL_CHECK(cl_err);
    printf("  Kernel 'fill_vectors' скомпилирован: OK\n");

    // ========================================================
    // ЭТАП 5: Передаём hipMalloc указатели в OpenCL kernel
    //         через clSetKernelArgSVMPointer
    //
    //         КЛЮЧЕВОЙ МОМЕНТ: мы НЕ используем clSVMAlloc!
    //         Память выделена hipMalloc. Указатель передаётся
    //         напрямую. OpenCL kernel пишет в VRAM GPU.
    // ========================================================
    print_separator();
    printf("ЭТАП 5: OpenCL kernel заполняет vec_a и vec_b\n");
    printf("        (указатели из hipMalloc → clSetKernelArgSVMPointer)\n");
    print_separator();

    printf("  Передаём d_vec_a (%p) → arg 0\n", (void*)d_vec_a);
    CL_CHECK(clSetKernelArgSVMPointer(ocl_kernel, 0, d_vec_a));

    printf("  Передаём d_vec_b (%p) → arg 1\n", (void*)d_vec_b);
    CL_CHECK(clSetKernelArgSVMPointer(ocl_kernel, 1, d_vec_b));

    int n = VEC_SIZE;
    CL_CHECK(clSetKernelArg(ocl_kernel, 2, sizeof(int), &n));

    // clEnqueueSVMMap/Unmap для указателей из hipMalloc на gfx1201 (ROCm OpenCL)
    // даёт SIGSEGV в libamdocl64 — пропускаем: буферы уже в VRAM, ядро пишет напрямую.

    // Запускаем OpenCL kernel
    size_t global_size = VEC_SIZE;
    CL_CHECK(clEnqueueNDRangeKernel(cl_queue, ocl_kernel, 1,
                                     nullptr, &global_size, nullptr,
                                     0, nullptr, nullptr));
    CL_CHECK(clFinish(cl_queue));

    printf("  OpenCL kernel выполнен: OK\n");
    printf("  vec_a должен быть: {10, 20, 30, ..., 100}\n");
    printf("  vec_b должен быть: {1, 2, 3, ..., 10}\n");

    // ========================================================
    // ЭТАП 6: HIP kernel читает vec_a и vec_b,
    //         суммирует в vec_c
    //
    //         Те же указатели! Та же физическая VRAM!
    //         НОЛЬ копирования между OpenCL и HIP!
    // ========================================================
    print_separator();
    printf("ЭТАП 6: HIP kernel суммирует vec_c = vec_a + vec_b\n");
    printf("        (читает данные, записанные OpenCL)\n");
    print_separator();

    // Убеждаемся что OpenCL закончил (уже сделали clFinish)
    // Запускаем HIP kernel
    hip_vector_add<<<1, VEC_SIZE>>>(d_vec_a, d_vec_b, d_vec_c, VEC_SIZE);
    HIP_CHECK(hipDeviceSynchronize());

    printf("  HIP kernel выполнен: OK\n");

    // ========================================================
    // ЭТАП 7: Копируем результаты на host и проверяем
    // ========================================================
    print_separator();
    printf("ЭТАП 7: Проверка результатов\n");
    print_separator();

    int h_a[VEC_SIZE], h_b[VEC_SIZE], h_c[VEC_SIZE];

    HIP_CHECK(hipMemcpy(h_a, d_vec_a, VEC_SIZE * sizeof(int),
                         hipMemcpyDeviceToHost));
    HIP_CHECK(hipMemcpy(h_b, d_vec_b, VEC_SIZE * sizeof(int),
                         hipMemcpyDeviceToHost));
    HIP_CHECK(hipMemcpy(h_c, d_vec_c, VEC_SIZE * sizeof(int),
                         hipMemcpyDeviceToHost));

    printf("\n  ┌───────┬────────────┬────────────┬────────────┬──────────┐\n");
    printf("  │   i   │  vec_a[i]  │  vec_b[i]  │  vec_c[i]  │ expected │\n");
    printf("  │       │ (OpenCL)   │ (OpenCL)   │ (HIP sum)  │  a+b     │\n");
    printf("  ├───────┼────────────┼────────────┼────────────┼──────────┤\n");

    int errors = 0;
    for (int i = 0; i < VEC_SIZE; i++) {
        int expected = (i + 1) * 10 + (i + 1); // a[i] + b[i]
        const char* status = (h_c[i] == expected) ? "  ✓" : "  ✗ FAIL";

        printf("  │  %2d   │    %4d    │    %4d    │    %4d    │  %4d %s│\n",
               i, h_a[i], h_b[i], h_c[i], expected,
               (h_c[i] == expected) ? " ✓ " : "✗! ");

        if (h_c[i] != expected) {
            errors++;
        }
    }

    printf("  └───────┴────────────┴────────────┴────────────┴──────────┘\n");

    // ========================================================
    // ЭТАП 8: Итоговый отчёт
    // ========================================================
    printf("\n");
    print_separator();
    printf("ИТОГОВЫЙ ОТЧЁТ\n");
    print_separator();

    printf("  GPU:                 %s (%s)\n", props.name, props.gcnArchName);
    printf("  OpenCL device:       %s\n", dev_name);
    printf("  OpenCL version:      %s\n", dev_ver);
    printf("  Аллокация:           hipMalloc (VRAM)\n");
    printf("  Передача в OpenCL:   clSetKernelArgSVMPointer\n");
    printf("  clSVMAlloc:          НЕ используется\n");
    printf("  cl_mem:              НЕ используется\n");
    printf("  CL_MEM_USE_HOST_PTR: НЕ используется\n");
    printf("  Копирование GPU→GPU: НЕТ (zero-copy)\n");
    printf("\n");
    printf("  d_vec_a:  %p (hipMalloc → OpenCL write → HIP read)\n",
           (void*)d_vec_a);
    printf("  d_vec_b:  %p (hipMalloc → OpenCL write → HIP read)\n",
           (void*)d_vec_b);
    printf("  d_vec_c:  %p (hipMalloc → HIP write)\n",
           (void*)d_vec_c);
    printf("\n");

    if (errors == 0) {
        printf("  ══════════════════════════════════════════\n");
        printf("  ✓ ТЕСТ ПРОЙДЕН: %d/%d элементов корректны\n",
               VEC_SIZE, VEC_SIZE);
        printf("  ══════════════════════════════════════════\n");
        printf("\n");
        printf("  ДОКАЗАНО: hipMalloc указатели работают в OpenCL\n");
        printf("  kernels через clSetKernelArgSVMPointer.\n");
        printf("  Один буфер в VRAM, два API, ноль копий.\n");
    } else {
        printf("  ✗ ТЕСТ НЕ ПРОЙДЕН: %d ошибок из %d\n",
               errors, VEC_SIZE);
    }

    printf("\n");

    // ========================================================
    // Cleanup
    // ========================================================
    clReleaseKernel(ocl_kernel);
    clReleaseProgram(prog);
    clReleaseCommandQueue(cl_queue);
    clReleaseContext(cl_ctx);

    HIP_CHECK(hipFree(d_vec_a));
    HIP_CHECK(hipFree(d_vec_b));
    HIP_CHECK(hipFree(d_vec_c));

    return (errors == 0) ? 0 : 1;
}
