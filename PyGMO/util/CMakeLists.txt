ADD_LIBRARY(_util SHARED util.cpp)
PYTHON_CPPMODULE(_util)
INSTALL(FILES __init__.py DESTINATION ${PYGMO_INSTALL_PATH}/util)
