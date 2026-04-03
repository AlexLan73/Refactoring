#pragma once
/**
 * @file all_test.hpp
 * @brief Все тесты модуля discriminator_estimates
 */

#include "test_discr_cg.hpp"
#include "test_discr_sd.hpp"
#include "test_discr_qa.hpp"
#include "test_discr_ea.hpp"
#include "test_discr_5ea.hpp"
#include "test_discr_common.hpp"
#include "test_discr_auto.hpp"

namespace discriminator_estimates_all_test {

inline void run() {
  discr_test_cg::run_all();
  discr_test_sd::run_all();
  discr_test_qa::run_all();
  discr_test_ea::run_all();
  discr_test_5ea::run_all();
  discr_test_common::run_all();
  discr_test_auto::run_all();

  std::cout << "\n========================================\n";
  std::cout << "ALL DISCRIMINATOR TESTS COMPLETE\n";
  std::cout << "========================================\n";
}

}  // namespace
