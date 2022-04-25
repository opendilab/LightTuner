from threading import Lock


class ValueProxyLock:
    def __init__(self):
        self.__rlock = Lock()
        self.__wlock = Lock()
        self.__rlock.acquire()
        self.__value = None

    def put(self, v):
        self.__wlock.acquire()
        self.__value = v
        self.__rlock.release()

    def get(self):
        self.__rlock.acquire()
        result, self.__value = self.__value, None
        self.__wlock.release()
        return result
