################################################################################
# Package: RingerCore
################################################################################

# Declare the package name:
atlas_subdir( RingerCore )

if( XAOD_STANDALONE )
  # We don't install RingerCore on GRID if we are on XAOD_STANDALONE mode
  if( NOT DEFINED $ENV{PanDA_TaskID} )
    # External dependencies:
    find_package( Boost COMPONENTS python )
    #find_package( ROOT COMPONENTS Core Hist Gpad Tree MathCore Hist MathMore RIO )
    find_package( ROOT COMPONENTS Core Hist RIO )

    find_package(OpenMP)
    if (OPENMP_FOUND)
        set (CMAKE_C_FLAGS "${CMAKE_C_FLAGS} ${OpenMP_C_FLAGS}")
        set (CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} ${OpenMP_CXX_FLAGS}")
    endif()

    atlas_add_library( RingerCoreLib
                       Root/*.cxx
                       PUBLIC_HEADERS RingerCore
                       INCLUDE_DIRS ${Boost_INCLUDE_DIRS} ${ROOT_INCLUDE_DIRS}
                       LINK_LIBRARIES ${Boost_LIBRARIES} ${ROOT_LIBRARIES}
                     )

  endif()
endif()


## Install files from the package:
atlas_install_python_modules( python/*.py python/parsers python/tex )
