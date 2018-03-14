
from enum import Enum,unique

@unique
class MsgType(Enum):
    INIT  = 0
    STAR  = 1
    OUT   = 2
    IN    = 3
    DONE  = 4
    MSG_COUNT = 5

    def __str__(self):
        return self.name


class SimMsg():
    """
    A Generic type for DEVS simulation messages
    """
    __type = None
    __from = None
    __time = None
    __param = None

    def __init__(self,mtype,mfrom,mtime,param=None):
        if not isinstance(mtype,MsgType):
            raise TypeError
        self.__type = mtype
        self.__from = mfrom
        self.__time = mtime
        self.__param = param

    def getType(self):
        return self.__type

    def getFrom(self):
        return self.__from

    def getTime(self):
        return self.__time

    def getParam(self):
        return self.__param

    def __str__(self):
        return "Msg(type={},from={},time={},param={}".format(self.__type,self.__from,self.__time,self.__param)

    def __eq__(self,other):
        return self.__type == other.getType() and self.__from == other.getFrom() and self.__time == other.getTime() and self.__param == other.getParam()

class InitMsg(SimMsg):
    def __init__(self,mfrom,mtime):
        super().__init__(MsgType.INIT,mfrom,mtime)

class StarMsg(SimMsg):
    def __init__(self,mfrom,mtime):
        super().__init__(MsgType.STAR,mfrom,mtime)

class InMsg(SimMsg):
    _x = None
    def __init__(self,mfrom,mtime,x):
        super().__init__(MsgType.IN,mfrom,mtime,x)
        self._x = x

class OutMsg(SimMsg):
    _y = None
    def __init__(self,mfrom,mtime,y):
        super().__init__(MsgType.OUT,mfrom,mtime,y)
        self._y = y

class DoneMsg(SimMsg):
    def __init__(self,mfrom,mtime):
        super().__init__(MsgType.DONE,mfrom,mtime)
    