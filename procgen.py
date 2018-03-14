from classic_devs import ClassicDevsCoupledModel
from sim_trace import setTraceFuncs

class CoupledGenerator(ClassicDevsCoupledModel):

    def subModelsSpecs(self):
        res = ( 
            ('generator','Generator','gen',1,"3"),   # gen has period 3
            ('processor','Processor','proc',1,"4")
            )  # proc has processing time 4
        return res

    def couplingsSpecs(self):
        res = (
            ('gen',('proc',)),              # gen to proc 
            ('proc',('self',)),             # proc upward to self
            )
        #res = (('gen',('proc',)),('proc',('self',)))
        return res

    def selectSpecs(self):
        # We must give priority to processor over generators such that 
        # they can accept a new job at the same time as complete the 
        # prvious one. 
        # Other selection policy are totally arbitrary
        # Given the combinatorics of this model, regexp are greatly helping
        # Notice also each spec is tried in order such that any ambiguity
        # is resolved by applying the first match. (Eg. the two forst rules
        # match {'proc:0', 'proc'} so the first rule is chosen)
        res = (\
            ({'proc', 'gen'}, 'proc'),\
            )
        return res


if __name__ == "__main__":
    from classic_devs import ClassicDevsRootCoordinator
    
    rc = ClassicDevsRootCoordinator(50.0,('procgen','CoupledGenerator','coupled',None))
    setTraceFuncs('*','*',rc,9,20)
    rc.start()

