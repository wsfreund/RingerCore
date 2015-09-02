#ifndef RINGERCORE_DEFINES_H
#define RINGERCORE_DEFINES_H

/**
 * Define DBG_LEVEL if this package is on debug mode
 **/
#if defined(RINGERCORE_DBG_LEVEL)
# ifndef DBG_LEVEL
# define DBG_LEVEL RINGERCORE_DBG_LEVEL
# endif
#endif

/**
 * Comment this to remove omp usage even if it is available on system
 **/
#define USING_MULTI_THREAD

#if defined(USING_MULTI_THREAD)
#include <omp.h>
#endif

/**
 * Do not change this macro
 **/
#define USE_OMP (defined(_OPENMP) && defined(USING_MULTI_THREAD))

#endif // RINGERCORE_DEFINES_H
