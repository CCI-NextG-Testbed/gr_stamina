INCLUDE(FindPkgConfig)
PKG_CHECK_MODULES(PC_STAMINA stamina)

FIND_PATH(
    STAMINA_INCLUDE_DIRS
    NAMES stamina/api.h
    HINTS $ENV{STAMINA_DIR}/include
        ${PC_STAMINA_INCLUDEDIR}
    PATHS ${CMAKE_INSTALL_PREFIX}/include
          /usr/local/include
          /usr/include
)

FIND_LIBRARY(
    STAMINA_LIBRARIES
    NAMES gnuradio-stamina
    HINTS $ENV{STAMINA_DIR}/lib
        ${PC_STAMINA_LIBDIR}
    PATHS ${CMAKE_INSTALL_PREFIX}/lib
          ${CMAKE_INSTALL_PREFIX}/lib64
          /usr/local/lib
          /usr/local/lib64
          /usr/lib
          /usr/lib64
          )

include("${CMAKE_CURRENT_LIST_DIR}/staminaTarget.cmake")

INCLUDE(FindPackageHandleStandardArgs)
FIND_PACKAGE_HANDLE_STANDARD_ARGS(STAMINA DEFAULT_MSG STAMINA_LIBRARIES STAMINA_INCLUDE_DIRS)
MARK_AS_ADVANCED(STAMINA_LIBRARIES STAMINA_INCLUDE_DIRS)
