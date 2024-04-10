#----------------------------------------------------------------
# Generated CMake target import file for configuration "Release".
#----------------------------------------------------------------

# Commands may need to know the format version.
set(CMAKE_IMPORT_FILE_VERSION 1)

# Import target "Kealib::kea" for configuration "Release"
set_property(TARGET Kealib::kea APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(Kealib::kea PROPERTIES
  IMPORTED_IMPLIB_RELEASE "${_IMPORT_PREFIX}/lib/libkea.lib"
  IMPORTED_LINK_DEPENDENT_LIBRARIES_RELEASE "hdf5-shared;hdf5_cpp-shared"
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/bin/libkea.dll"
  )

list(APPEND _cmake_import_check_targets Kealib::kea )
list(APPEND _cmake_import_check_files_for_Kealib::kea "${_IMPORT_PREFIX}/lib/libkea.lib" "${_IMPORT_PREFIX}/bin/libkea.dll" )

# Commands beyond this point should not need to know the version.
set(CMAKE_IMPORT_FILE_VERSION)
