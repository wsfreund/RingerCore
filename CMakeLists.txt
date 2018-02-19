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

		### Install python packages
		list(APPEND CMAKE_MODULE_PATH "${CMAKE_CURRENT_LIST_DIR}/cmake")

		include(SetupPythonPackage)

    setup_python_package( numpy 
    "https://github.com/numpy/numpy/releases/download/v1.14.0/numpy-1.14.0.tar.gz"
    "c573e2d2f26a5786d5198a660f87d8e4"
    #PATCH ${CMAKE_CURRENT_SOURCE_DIR}/cmake/patch-setup.cfg setup.cfg
    #ARG_DEPENDS scipy
  	 LOG_DOWNLOAD 0
  	 LOG_UPDATE 0
  	 LOG_CONFIGURE 0
  	 LOG_BUILD 0
  	 LOG_TEST 0
  	 LOG_INSTALL 1
    )

    #setup_python_package( scipy
    #"https://github.com/scipy/scipy/releases/download/v1.0.0/scipy-1.0.0.tar.gz"
    #"53fa34bd3733a9a4216842b6000f7316"
    # ARG_DEPENDS numpy
    #)
    #add_dependencies(scipy numpy)

  endif()
endif()


## Install files from the package:
atlas_install_python_modules( python/*.py python/parsers python/tex )
atlas_install_scripts( scripts/hadd_chunk.py )
