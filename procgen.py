from classic_devs import ClassicDevsCoupledModel
from sim_trace import setTraceFuncs

class CoupledGenerator(ClassicDevsCoupledModel):

    def subModelsSpecs(self):
        res = ( 
            ('generator','Generator','gen',1,"3"),      # gen has period 3
            ('processor','Processor','proc',1,"4"),     # proc has processing time 4
            )  
        return res

    def couplingsSpecs(self):
        res = (
            ('gen',('proc',)),              # gen to proc 
            ('proc',('self',)),             # proc upward to self
            )
        #res = (('gen',('proc',)),('proc',('self',)))
        return res

    def selectSpecs(self):
        res = (
            ({'proc', 'gen'}, 'proc'),      # Priority given to proc
            )
        return res


if __name__ == "__main__":
    from classic_devs import ClassicDevsRootCoordinator
    
    rc = ClassicDevsRootCoordinator(10.0,('procgen','CoupledGenerator','coupled',None))
    setTraceFuncs('*','*',rc,9,20)
    rc.start()

