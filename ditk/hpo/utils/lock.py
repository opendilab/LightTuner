from threading import Lock


class RunFailed(Exception):
    pass


class ValueProxyLock:
    def __init__(self):
        self.__rlock = Lock()
        self.__wlock = Lock()
        self.__rlock.acquire()
        self.__value = None

    def put(self, v):
        self.__wlock.acquire()
        self.__value = (True, v)
        self.__rlock.release()

    def fail(self, err):
        self.__wlock.acquire()
        self.__value = (False, err)
        self.__rlock.release()

    def get(self):
        self.__rlock.acquire()
        (success, obj), self.__value = self.__value, None
        self.__wlock.release()
        if success:
            return obj
        else:
            raise RunFailed(obj)
