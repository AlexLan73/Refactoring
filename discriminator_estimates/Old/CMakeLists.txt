cmake_minimum_required(VERSION 3.0)

set(PROJECT_NAME discr)
set(PROJECT_LANGUAGES C)
set(ROOT_PATH "../../..")

include(${ROOT_PATH}/build/General.cmake NO_POLICY_SCOPE)
project(${PROJECT_NAME} ${PROJECT_LANGUAGES})

set(SOURCES
  src/discrcg.c
  src/discrea.c
  src/discrqa.c
  src/discrsd.c
  src/discr_common.c
)
	
set(HEADERS
  include/discrcg.h
  include/discrea.h
  include/discrqa.h
  include/discrsd.h
  include/discr_common.h
  include/discr_types.h
)

add_library(${PROJECT_NAME} ${SOURCES} ${HEADERS})

make_dep_tree()
