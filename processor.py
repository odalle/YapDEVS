from classic_devs import ClassicDevsAtomicModel
from random import randint
from math import inf


class Processor(ClassicDevsAtomicModel):

    __period = None

    def __init__(self,name,period):
        """Constructor."""
        super().__init__(name)
        self.__period = period

    #
    #  PHASE: INIT
    #  
    def onInternalWhen_init(self,state):
        """At the beginning, switch from init to idle."""
        return ("idle", state)

    def onTaWhen_init(self,state):
        """Switch immediately from init to idle."""
        return 0

    def onOutWhen_init(self,state):
        """No output on init"""
        return None

    #
    #  PHASE: IDLE
    #  
    def onTaWhen_idle(self,state):
        """Passive state."""
        return inf

    def onExternalWhen_idle(self,state,elapsed,input):
        """Memorise job and switch to busy state."""
        #print("input={}".format(input))
        state['job']=input[1]['job']
        return ("busy",state)

    #
    #  PHASE: BUSY
    #  

    def onInternalWhen_busy(self,state):
        """Switch from busy to idle"""
        return ("idle", state)

    def onTaWhen_busy(self,state):
        """Stay for a fixed delay in busy state."""
        return self.__period

    def onOutWhen_busy(self,state):
        """Output the job initially received."""
        return (('job',{'job': state['job']}))

    
    def onExternalWhen_busy(self,state,elapsed,input):
        """Ignore input while busy."""
        # Update stats
        state['missed']=state.get('missed',0)+1
        return False  # Continue without changing phase
