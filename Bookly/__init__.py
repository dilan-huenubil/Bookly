try:
    import MySQLdb  # Intenta usar la librería nativa en C++ (Tú y Render)
except ImportError:
    import pymysql  # Si falla, usa la alternativa en Python puro (Rodrigo)
    pymysql.version_info = (1, 4, 3, "final", 0)
    pymysql.install_as_MySQLdb()