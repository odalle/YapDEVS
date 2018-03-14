from classic_devs import ClassicDevsAtomicModel
from math import inf

class Generator(ClassicDevsAtomicModel):
    """A simple generator.
    
    This model produces periodically an output on port 'job' after waiting
    for the requested period. It produced its first output after the period
    has elapsed.

    @parameter : the generator period
    """
    __period = None

    def __init__(self,name,period):
        """ Constructor."""
        super().__init__(name)
        self.__period = period
 
    #
    #  PHASE: INIT
    #  
    def onInternalWhen_init(self,state):
        """Switch next to phase 'default'"""
        return ('default', state)

    def onOutWhen_init(self,state):
        """No output when reaching end of phase."""
        return None

    def onTaWhen_init(self,state):
        """Transient state."""
        return 0.0

    #
    #  PHASE: DEFAULT
    #  
    def onInternalWhen_default(self,state):
        """Return to 'default' pahse for ever."""
        return ("default", state)

    def onTaWhen_default(self,state):
        """Set duration of 'default' phase to period."""
        return self.__period

    def onOutWhen_default(self,state):
        """Outputs a message of type dict on port 'job'."""
        return (('job', {'job': self.getPath()}))

    

 