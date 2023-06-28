from loguru import logger

from utils.cache import TepCache


class Step:
    """
    测试步骤，泛化调用
    """

    def __init__(self, name: str, action, cache: TepCache):
        logger.info("----------------" + name + "----------------")
        action(cache)
