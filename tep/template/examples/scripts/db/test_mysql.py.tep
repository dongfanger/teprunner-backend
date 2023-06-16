import allure
from loguru import logger

from utils.dao import print_db_table, mysql_engine

try:
    import pandas as pd
except ModuleNotFoundError:
    pass


@allure.title("连接数据库")
def test_mysql(env_vars):
    sql = "select 1 from dual"
    db_type = "mysql"
    engine = mysql_engine(env_vars["db"][db_type]["host"],
                          env_vars["db"][db_type]["port"],
                          env_vars["db"][db_type]["user"],
                          env_vars["db"][db_type]["password"],
                          env_vars["db"][db_type]["db"])
    data = pd.read_sql(sql, engine)
    logger.info(print_db_table(data))
