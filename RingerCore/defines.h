#ifndef RINGERCORE_DEFINES_H
#define RINGERCORE_DEFINES_H

/**
 * Define DBG_LEVEL if this package is on debug mode
 **/
#if defined(RINGERCORE_DBG_LEVEL)
# ifndef DBG_LEVEL
#   define DBG_LEVEL RINGERCORE_DBG_LEVEL
# endif
#endif

/**
 * Comment this to remove omp usage even if it is available on system
 **/
#if !defined(__CINT__) && !defined(__CLING__)
//# define USING_MULTI_THREAD
#endif

#if defined(USING_MULTI_THREAD)
# include <omp.h>
#endif

/**
 * Do not change this macro
 **/
#define USE_OMP (defined(_OPENMP) && defined(USING_MULTI_THREAD))

//the following are UBUNTU/LINUX ONLY terminal color codes.
#define RESET       "\033[0m"
#define NORMAL      RESET
#define BLACK       "\033[90m"             /* Black */
#define RED         "\033[91m"             /* Red */
#define GREEN       "\033[92m"             /* Green */
#define YELLOW      "\033[93m"             /* Yellow */
#define BLUE        "\033[94m"             /* Blue */
#define MAGENTA     "\033[95m"             /* Magenta */
#define CYAN        "\033[96m"             /* Cyan */
#define DARKCYAN    "\033[36m"             /* Dark Cyan */
#define GRAY        "\033[30m"             /* Gray */
#define WHITE       "\033[97m"             /* White */
#define BOLDBLACK   "\033[1m\033[90m"      /* Bold Black */
#define BOLDRED     "\033[1m\033[91m"      /* Bold Red */
#define BOLDGREEN   "\033[1m\033[92m"      /* Bold Green */
#define BOLDYELLOW  "\033[1m\033[93m"      /* Bold Yellow */
#define BOLDBLUE    "\033[1m\033[94m"      /* Bold Blue */
#define BOLDMAGENTA "\033[1m\033[95m"      /* Bold Magenta */
#define BOLDCYAN    "\033[1m\033[96m"      /* Bold Cyan */
#define BOLDWHITE   "\033[1m\033[97m"      /* Bold White */


#endif // RINGERCORE_DEFINES_H
