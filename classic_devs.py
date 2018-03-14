#!/usr/bin/env python
#  -*- encoding: utf-8 -*-

"""
file:       classic_devs.py
author:     Olivier Dalle
contact:    olivier.dalle@unice.fr
licence:    (c) 2018. This software can be reused and redistributed according to the
            terms of the license CeCILL v2.1 of 2013-06-21. (compliant with GNU GPL)
            See here: http://www.cecill.info/licences/Licence_CeCILL_V2.1-en.html
version:    1.0
description: This module provides the elements for building Classic DEVS models
            (with ports) simulations. It is mostly meant for educational purpose
            and, therefore, should not be relied on for complex simulations.

            According to the specification, Classic DEVS models can be defined 
            either as coupled or atomic models.

            Atomic models must extend the `ClassicDevsAtomicModel` class and coupled
            models must extend the `ClassicDevsCoupledModel` according to the following
            rules.

            :Atomic Models:

            A DEVS atomic model is a tuple defined as

            M = < X,Y,S, delta_int, delta_ext, ta, lamdda >
            
            where X and Y are the sets of input and output values, S the total state, 
            and the reminder are functions computing respectively the state after
            an internal transition (delta_int), after an external transition (delta_ext),
            the time to spend in the nes state (ta) and the output to be produced just
            before an internal transition.

            Even though it is not explicitely part of the DEVS specifications, our
            implementation assumes that the state of an Atomic model is composed of 
            a phase and a set of state variables, implememted respectively as a
            string and a dictionary. 
            
            Given that a model is always expeted to have a phase, our atomic model 
            implementation forces the modeler to always link explcitely the model 
            definitions to the phase to which they apply.
            
            Each atomic model must implement callbacks functions corresponding to
            the functions of a Classic DEVS model specification, suffixed with the
            name of the phase to which they apply. For example, the external
            transition function to apply when a model is in a phase named "active"
            is a callback named `onExternalWhen_active`.

            The callback functions may be of 4 types:
            - onInternalWhen_xxxx() : internal transition (delta_int in DEVS)
            - onExternalWhen_xxxx() : external transition (delta_ext in DEVS)
            - onTaWhen_xxxx()       : time advance (ta in DEVS)
            - onOutWhen_xxxx()      : output function (lambda in DEVS)

            More details are given about these callbacks in the docstring of the
            class `ClassicDevsAtomicModel`, eg. using:
                >>> help(ClassicDevsAtomicModel)

            The rationale for these "phased-suffixed" functions is to avoid the
            modeler the repetitive and prone-to-error task of listing all the cases
            in a big if/elif/else statement. The function names are automatically 
            generated, such that if a case is missingm the corresponding function
            is also missing, which triggers an error. 
            On the contrary, missing a case in a big if statement might go 
            unnoticed and end-up in a harder to diagnose error.

            Notice that all models start in a phase called "init", which
            means that at the very least, every model is required to implement the 
            `onTaWhen_init()` function.

            :Coupled Models:

            A DEVS coupled model is a tuple defined as

            C = < X,Y,D, M, Z, select > 
            
            where X and Y are the sets of input and output values, D is a set of
            sub-model names, M is a set model specfications, Z is a translation 
            function that maps outputs to inputs, and select is a tie-breaking
            function.

            The actual coding of such a model only requires three functions to be
            defined in a derived class of the abstract class `ClassicDevsCoupledModel`:

            - `subModelSpecs` : returns a sequence (list or tuple) of quintuplets,
            one for each submodel that is part of the coupled model. Each quintuplet
            is a model specification composed of the foollowing elements
            
            model_spec = (mmod, mclass, name, count, initparm )

            with:
                - mmod: the name of the python module containing the class definition
                of the coupled model
                - mclass: the class name of the model. Together mmod.mclass form one 
                element of the M set of the DEVS coupled definition
                - name: the name of the sub-model, which correspond to an element of 
                the D set in the DEVS coupled definition
                - count: the number of identical copies of the same model to 
                instantiate. If count > 1, then the actual name of each copy is 
                suffixed by the copie order. 
                For example, if name = "proc" and count=2, then we end up with 
                the two names "proc:0" and "proc:1".
                - initparm : an initial parameter value (any type) passed to the 
                class constructor. 

            - `couolingsSpecs` : returns a sequence (list or tuple) of pairs
            (src_spec, dst_spec) that defines the couplings of a coupled model.
            Couplings can be categorized in 3 kinds: External Input Couplings (EIC),
            External Output Couplings (EOC) and Internal Couplings (IC).
            When src_spec = `self` then the pair is an EIC specification; when 
            dst_spec = `self`, then the pair is an EOC spec; otherwise, the pair
            is an IC spec. 
            When src_spec is not 'self', then it can be of two forms:
              - a single name, eg. "proc" or "proc:0"
              - a range-suffixed name, that uses the same convention as the
              python slicing. Eg. proc[1:3] stands for the set {'proc:1', 
              'proc:2'} (notice the righ bound is excluded, as Python does)
            When dst_spec is not 'self', then it is a tuple of elements of
            the same type as src_spec (ie. a single name or a range-suffixed
            name)
            For example let's decode the following spec:
                ('gen[2:4]', ('proc[0:2]', proc)) 
            It means that the outputs of the two submodels named 'gen:2' and 
            'gen:3' are connected to the inputs of the three submodels named
            'proc:0', 'proc:1', and 'proc'.

            - `selectSpecs` : defines the tie-breaking function. 
            This function return a sequence (list or tuple) of pairs
            (set,winner), in which set gives a list of candidates and
            winner tells which of the candidates is the winner.
            The classic DEVS specification requires an enumeration of all 
            the potential conflicts, which is potentially a high 
            combintorics enumeration.
            To ease (And shorten) this enumeration, we accept python 
            regular expressions, and use a priority rule: the first
            pair of the sequence that matches the requested set of 
            candidates is chosen and any subsequent pair is ignored.
            Regular expressions can be used to describe the set element
            of the pair. For example the set {'proc:0', '.*'} matches 
            any set of 2 or more elements that contains the name 'proc:0'.
            Indeed, an important matching rule is that each element
            of the set given in the pair must match at least on element
            of the set of candidates.
            For example, {'proc.*', '.*'} matches {'proc:0', 'proc:1'},
            but not {'proc:0'} because the second expression, ',*' does
            not match any element once 'proc:0' is matched with 'proc.*'.
            
"""


from sim_trace import trace_transition, invalid_attribute, trace_select, TraceDict
from sim_msg import MsgType, SimMsg, OutMsg, InitMsg, StarMsg, DoneMsg, InMsg
from re import match, fullmatch


class Simulator():
    """ Anchor type for all simulator types.

        Abstract class.

        All simulator and coordinator object inherit this type, which
        helps finding type mismatch errors.
    """
    def __init__(self):
        pass

class Model():
    """ Anchor type for all model types.

        Abstract class.

        All model objects inherit this type, which
        helps finding type mismatch errors.

        Attributes:
        - __name:       model name
    """
    __name = None

    def __init__(self,name):
        self.__name = name

    def __str__(self):
        return self.__name

    def getName(self):
        return self.__name


class HierarchicalModel(Model):
    """ Anchor type for all hieraerchical model types.

        Abstract class. Extends Model.

        All models belonging to a model hierarchy inherit this type.
        The path attribute holds a string the represents the path to
        the model in the hierarchy, using the `/` separator at each
        level of the hierarchy. 
        
        For example, `/foo/bar` represents the path to a model named 
        `bar` which is a sub-model of model `foo` in the hierarchy.

        Attributes:
        - __path:   a string path to represent the location of the 
                    model in the hierarchy
    """
    __path = None

    def __init__(self,name):
        """Constructor."""
        super().__init__(name)


    def build(self,path):
        """Builds the path name recursively."""
        self.__path = path + '/' + self.getName()

    def getPath(self):
        """Private attribute accessor."""
        return self.__path


class ClassicDevsAtomicModel(HierarchicalModel):
    """ Implement Classic DEVS atomic model.

    Abstract class. Extends Model.

    Classic DEVS models own a `phase` and `state`. `phase` is a string 
    that defines the automaton state of the model. `state` is a dictionary
    that holds additional state vartiables.

    This class implements an event-driven pattern that requires callbacks 
    for functions of the DEVS model specification to be defined for each 
    phase as follows, where `xxxx` is the current phase:
    - delta_int(s): `onInternalWhen_xxxx(state) -> (phase,state)`
     
     :return:: the new `phase` and `state` reached after internal transition.

    - delta_ext(s,e,x): `onExternalWhen_xxxx(state,elapsed,input) -> (phase,state) | False`
    
     :return:: the new `phase` and `state` reached after external transition 
     or `False` if the model is to continue in the same phase without changing
     state (which means the input is ignored).

    - ta(s): `onTaWhen_xxxx(state) -> duration`

     :return:: the `duration` the model is to stay in the current state after the
     internal transition

    - lambda(s): `onOutWhen_xxxx(state) -> (port, msg) | None`

     :return:: a `port` and `msg` pair corresponding to the output produced by
     the model immediately BEFORE switching to the new state when the time of
     the internal transition is reached. The `port` parameter is a string value
     and the `msg` parameter a dictionary. 
     
     The model can also produce no output, in which case the `None` value is 
     returned.

    :Example:
    A derived model with two phases `"active"` and `"passive"` COULD 
    define the following model methods :
    - `onInternalWhen_active(state)`
    - `onInternalWhen_passive(state)`
    - `onExternalWhen_active(state,elapsed,input)`
    - `onExternalWhen_passive(state,elapsed,input)`
    - `onTaWhen_active(state)`
    - `onTaWhen_passive(state)`
    - `onOutWhen_active(state)`
    - `onOutWhen_passive(state)`

    However, the definition of some of these methods may be optionnal. For 
    example, if the model does not receive external input, it is not required
    to define the `onExternalWhen_xxxx` callback(s).
    
    """
    __phase = None
    __state = None

    def __init__(self,name,phase="init",state=None):
        """ Constructor.

        :Parameters:
        - name:     Model super-class attribnute (string)
        - phase:    phase attribute (string)
        - state:    additional state variables (dict)
        """
        if state is None: state = TraceDict()
        if not isinstance(state,dict): raise TypeError
        super().__init__(name)
        self.__phase = phase
        self.__state = state

    def build(self,path):
        """Builds the path name recursively."""
        super().build(path)
        if isinstance(self.__state, TraceDict):
            self.__state.setPath(self.getPath())

    def getPhase(self):
        """ Private atrribute accessor. """
        return self.__phase

    def getState(self):
        """ Private atrribute accessor. """
        return self.__state

    @trace_transition('dint')   # Trace calls with label 'dint'
    def __onInternal(self, phase, state):
        """Callback dispatcher function for delta_int. """
        method_name = "onInternalWhen_"+phase
        method = getattr(self, method_name, \
            lambda s : exec("raise Exception('missing method implementation \"" \
                +method_name+"\":\\nAdd declaration to your model eg:\\n\\tdef " \
                +method_name+"(self,state):\\n\\t...')\nraise NotImplementedError()") )
        return method(state)

    @trace_transition('dext')   # Trace calls with label 'dext'
    def __onExternal(self, phase, state,elapsed,input):
        """Callback dispatcher function for delta_ext. """
        method_name = "onExternalWhen_"+phase
        method = getattr(self, method_name, \
            lambda s,e,x : exec("raise Exception('missing method implementation \"" \
                +method_name+"\":\\nAdd declaration to your model eg:\\n\\tdef " \
                +method_name+"(self,state,elapsed,input):\\n\\t...')\nraise NotImplementedError()" ))
        #print ("method={}".format(method))
        return method(state,elapsed,input)

    @trace_transition('  ta')   # Trace calls with label '  ta'
    def __onTa(self,phase, state):
        """Callback dispatcher function for ta(s). """
        method_name = "onTaWhen_"+phase
        method = getattr(self, method_name, \
            lambda s : exec("raise Exception('missing method implementation \"" \
                +method_name+"\":\\nAdd declaration to your model eg:\\n\\tdef " \
                +method_name+"(self,state):\\n\\t...')\nraise NotImplementedError()"  ) )
        return method(state)

    @trace_transition(' out')   # Trace calls with label ' out'
    def __onOut(self,phase,state):
        """Callback dispatcher function for lambda/out(s). """
        method_name = "onOutWhen_"+phase
        method = getattr(self, method_name, \
            lambda s : exec("raise Exception('missing method implementation \"" \
                +method_name+"\":\\nAdd declaration to your model eg:\\n\\tdef " \
                +method_name+"(self,state):\\n\\t...')\nraise NotImplementedError()" ))
        return method(state)

    
    def delta_int(self):
        """ DEVS Internal transition. Computes the new state to switch into when sigma 
        reaches 0.

        This method is a PROCEDURE that changes the phase and state attributes 
        as a side effect. It DOES NOT return the state as in the the DEVS formalism 
        specification.

        :Parameters:    None (uses phase and state attributes)

        :Return:        None (updates phase and state attributes)
        """
        (self.__phase, self.__state) = self.__onInternal(self.__phase, self.__state)

    def delta_ext(self, elapsed, input):
        """ DEVS External transition. Computes the new state to switch into when receiving
        an input.

        This method is a PROCEDURE that changes the phase and state attributes 
        as a side effect. It DOES NOT return the state as in the DEVS formalism 
        specification. However, it does return whether it changed the phase or not. 

        :Parameters:    
        - `elapsed`:    Time elapsed in current state since the last transition.
        - `input`:      a `(port,msg)` pair if the model produces an output, `None` otherwise.

        :Return:        True if state was changed.
        """
        ext_result = self.__onExternal(self.__phase, self.__state, elapsed, input)
        if bool(ext_result) :
            (self.__phase, self.__state) = ext_result
        return bool(ext_result)

    def ta(self):
        """Returns the time advance value, ie. how long to stay in the given state."""
        return self.__onTa(self.__phase,self.__state)       

    def out(self):
        """ DEVS lambda output function.

        Returns the message to be placed on output just BEFORE the state changes on an 
        INTERNAL transition. 
        Note: This function is named out rather than lambda, because `lambda` is a reserved
        keyword in Python.

        :Parameters:    None (uses phase and state attributes)

        :Return:        The returned value is either a tuple `(port,msg)` where `port` 
                        is a string and `msg` a dictionary, or `None` if the model 
                        produces no output.
        """
        return self.__onOut(self.__phase,self.__state)

    def __str__(self):
        return "{}({})".format(self.__class__.__name__,self.getPath())

class ClassicDevsAbstractSimulator(Simulator):
    """ Implements the Classic DEVS with port simulator following the abstract
    simulator description given by Tendeloo and Vangheluwe's Introduction to 
    classic DEVS (https://arxiv.org/pdf/1701.07697.pdf).
    """
    __msg_queue = None
    __parent    = None
    __model     = None
    __time_last = None
    __time_next = None

    def __init__(self, parent, model):
        """Constructor.

        :Parameters:
        - parent:   Parent simulator in the hierarchy.
        - model:    DEVS model associated to this simulator.    
        """
        super().__init__()
        if not isinstance(parent,Simulator): raise TypeError
        if not isinstance(model, Model): raise TypeError
        self.__msg_queue = []
        for __ in  range(len(MsgType)): self.__msg_queue.append([])
        #print("setting self.__parent to {}".format(parent))
        self.__parent = parent
        #print("setting {}.__model to {}".format(self,model))
        self.__model  = model

    def getParent(self):
        """ Private atrribute accessor. """
        return self.__parent

    def getModel(self):
        """ Private atrribute accessor. """
        return self.__model

    def getTimeLast(self):
        """ Private atrribute accessor. """
        return self.__time_last

    def getTimeNext(self):
        """ Private atrribute accessor. """
        return self.__time_next

    def updateTimes(self,last,next):
        """ Combined write accessor for time_last and time_next attributes."""
        self.__time_last = last
        self.__time_next = next

    def queue_msg(self,msg):
        """Queue a new synchronization message.

        Message are queued in a disctinct sub-queue according to the message type, such that
        message can then be processed with priorities corresponding to their type.
        """
        if not isinstance(msg,SimMsg):
            raise TypeError
        #print("{}({}).queue_msg({})".format(self.__class__.__name__,self.__model.getPath(),msg))
        self.__msg_queue[msg.getType().value].append(msg)
        #print("__msg_queue[{}]={}".format(msg.getType().value,self.__msg_queue[msg.getType().value]))
        
    def activate(self):
        """Activate this model: all pending messages for the current time are 
        processed until none is left.

        Each message found in the queue is dispatched to a callback according to its
        type.
        """
        for msg_type in range(MsgType.MSG_COUNT.value):
            msgs = list(self.__msg_queue[msg_type])
            if len(msgs) == 0: continue
            self.__msg_queue[msg_type] = []
            method_name = "on"+MsgType(msg_type).name
            method = getattr(self, method_name, \
                    lambda s : exec("raise Exception('missing method implementation for \""+method_name+"\"')"))
            for msg in msgs:
                #print("{}({}).activate(): calling {} with msg={}".format(self.__class__.__name__,self.__model.getPath(),method_name,msg))
                method(msg.getFrom(), msg.getTime(), msg.getParam())
                #self.__msg_queue[msg.getType().value].remove(msg)

    def onINIT(self,mfrom,mtime,param):
        """Callback method for INIT message.
        
        Pure virtual method. (To be implemented in derived class.)
        """
        raise NotImplementedError

    def onSTAR(self,mfrom,mtime,param):
        """Callback method for STAR message.
        
        Pure virtual method. (To be implemented in derived class.)
        """
        raise NotImplementedError

    def onIN(self,mfrom,mtime,param):
        """Callback method for IN message.
        
        Pure virtual method. (To be implemented in derived class.)
        """
        raise NotImplementedError

    def onOUT(self,mfrom,mtime,param):
        """Callback method for OUR message.
        
        Pure virtual method. (To be implemented in derived class.)
        """
        raise NotImplementedError

    def onDONE(self,mfrom,mtime,param):
        """Callback method for DONE message.
        
        Pure virtual method. (To be implemented in derived class.)
        """
        raise NotImplementedError


class ClassicDevsAtomicSimulator(ClassicDevsAbstractSimulator):

    def __init__(self, parent, model):
        super().__init__(parent,model)

    def onINIT(self,mfrom,mtime,param):
        #print("onInit: setting time_last to:{}".format(mtime))
        self.updateTimes(mtime, mtime + self.getModel().ta())
        #print("{}.onIINIT(from={},time={},param={}); parent={}; queueing DoneMsg".format(self,mfrom,mtime,param,self.getParent()))
        self.getParent().queue_msg(DoneMsg(self,self.getTimeNext()))

    def onSTAR(self,mfrom,mtime,param):
        if mtime != self.getTimeNext(): 
            # I think this is an error: if this happens, we dont notify the parent
            # that we are done
            raise Exception('Star message requested at a time that is not reached yet!')
        out = self.getModel().out()
        if not out is None:
            self.getParent().queue_msg(OutMsg(self,mtime,out))
        self.getModel().delta_int()
        #print("onStar: setting time_last to:{}".format(mtime))
        self.updateTimes(mtime, mtime+ self.getModel().ta())
        #print("{}.onSTAR(from={},time={},param={}); parent={}); queueing DoneMsg".format(self,mfrom,mtime,param,self.getParent()))
        self.getParent().queue_msg(DoneMsg(self,self.getTimeNext()))

    def onIN(self,mfrom,mtime,param):
        if not (self.getTimeLast() <= mtime <= self.getTimeNext()):
            raise Exception('In message requested at wrong time')
        elapsed = mtime - self.getTimeLast()
        if self.getModel().delta_ext(elapsed,param):
            self.updateTimes(mtime, mtime+ self.getModel().ta())
        self.getParent().queue_msg(DoneMsg(self,self.getTimeNext()))

    def onDONE(self,mfrom,mtime,param):
        #print("onDONE({},{},{},{})".format(self,mfrom,mtime,param))
        raise NotImplementedError

    def __repr__(self):
        return "{}(model={}, parent={})".format(self.__class__.__name__,self.getModel(),self.getParent())

class ClassicDevsCoupledModel(HierarchicalModel):
    __sub_models = None
    __couplings = None
    __select_specs = ()

    def __init__(self,name):
        self.__sub_models = dict()
        self.__couplings = dict()
        super().__init__(name)

    @invalid_attribute
    def _sub_models(self):
        pass

    @invalid_attribute
    def _subModels(self):
        pass

    @invalid_attribute
    def _couplings(self):
        pass

    @invalid_attribute
    def _select_specs(self):
        pass

    @invalid_attribute
    def _selectSpecs(self):
        pass

    def getSubModels(self):
        return self.__sub_models

    def getCouplings(self):
        return self.__couplings

    def getSelectSpecs(self):
        return self.__select_specs

    def __makeInstanceSpec(self,mtype,mname,args):
        instance_spec = mtype+'("'+mname+'"'
        if args: 
            instance_spec += ','+args
        instance_spec += ')'
        return instance_spec

    def __instantiateModel(self,mmod,mtype,spec):
        exec('from '+mmod+' import '+mtype)
        model=eval(spec)
        return model

    def __createModel(self,mmod,mtype,mname,args):
        instance_spec = self.__makeInstanceSpec(mtype,mname,args)
        model=self.__instantiateModel(mmod,mtype,instance_spec)
        if not issubclass(model.__class__,Model):
            raise TypeError("Unable to create model: Invalid model type ("+mtype+")")
        if mname in self.__sub_models.keys():
            raise Exception("A model named %s exist already!"%(mname))
        self.__sub_models[mname] = model    

    def __createSubModels(self):
        model_specs = self.subModelsSpecs()
        if model_specs is []:
            raise Exception("Missing model specs!") 
        for (mmod,mtype,mname,count,args) in model_specs:
            if count > 1:
                for i in range(count):
                    self.__createModel(mmod,mtype,mname+":"+str(i),args)
            else:
                self.__createModel(mmod,mtype,mname,args)

    def __createCoupling(self,src, dst):
        previous = self.__couplings.get(src,[])
        if not dst in previous:
            previous.append(dst)
        self.__couplings[src] = previous

    def __findMatchingNumberedModels(self,name,first,last):
        """ 
        Scan subModels to find names matching
        either a singleton or a numbered model
        in range [first,last[
        """
        if name == 'self': return ['self']
        regexp = r"^(?P<base>\w+)(:(?P<num>\d+))?"
        matches = []
        for mname in self.__sub_models.keys():
            m=match(regexp,mname)
            base = m.group('base')
            num = m.group('num')
            if m:
                if first and last and num and base == name:
                    # if a numbered model is found
                    # keep only if number in spec range
                    if first <= num < last:
                        matches.append(mname)
                elif not first and name == mname:
                    matches.append(mname)
        return matches

    def __decodeRangeSpec(self,spec):
        m = match(r"^(?P<name>\w+(:\d+)?)(\[(?P<first>\d+):(?P<last>\d+)])?$",spec)
        if m is None:
            raise Exception("Invalid coupling spec src '%s' error in model %s."%(spec,self.__name))
        return (m.group('name'), m.group('first'), m.group('last'))


    def __createCouplings(self):
        coupling_specs = self.couplingsSpecs()
        for coupling in coupling_specs:
            src,dsts = coupling[0],coupling[1]
            (src_name, src_first, src_last) = self.__decodeRangeSpec(src)
            src_matches = self.__findMatchingNumberedModels(src_name,src_first,src_last)
            for dst in dsts:
                (dst_name, dst_first, dst_last) = self.__decodeRangeSpec(dst)
                dst_matches = self.__findMatchingNumberedModels(dst_name,dst_first,dst_last)         
                # Loop on pairing all src with dsts
                for src_match in src_matches:
                    for dst_match in dst_matches:
                        self.__createCoupling(src_match,dst_match)

    def build(self,path):
        super().build(path)
        self.__createSubModels()
        self.__createCouplings()
        self.__select_specs = self.selectSpecs()
        for model in self.__sub_models.values():
            model.build(self.getPath())

    @trace_select
    def select(self,nameSet):
        """ DEVS coupled model `select` function.
        """
        # First we try exact matching
        for spec in self.__select_specs:
            if nameSet == spec[0]:
                return spec[1]

        # Then we try regexp matching
        def gather_match_from_spec(spec):
            """Returns a list of all elements of surrounding function's
            nameSet parameter that match a given spec. For each element
            of spec, at least one match must be found in nameSet or the
            spec is considered a mismatch.
            """
            match_found = []
            for spec_item in spec[0]:
                match_in = []
                for n in nameSet:
                    if fullmatch(spec_item,n) is not None:
                        match_in.append(n)
                if len(match_in) == 0:
                    return None
                match_found += match_in
            return match_found

        for spec in self.__select_specs:
            match_found = gather_match_from_spec(spec)
            if match_found is None: continue
            match_set = set(match_found)  
            if nameSet == match_set:
                return spec[1]
        return False

    def subModelsSpecs(self):
        """
        This method must return an array of tuples (type, model_name,count) in
        which type is the model type (eg. CoupledDevsModel or AtomicDevsModel)
        and model_name is string defining the componenent name, and count is the
        number of instances to create. 
        If count is 1, only one instance is created with name model_name.
        If count is given, each instance is named using the pattern name:<k>
        in which <i> is an integer given by range(count).
        """
        raise NotImplementedError()

    def couplingsSpecs(self):
        """
        This method must return an array of tuples (model_name, dests) in
        which model_name the name of a submodel (or "self") and dest is an
        array of model_names (os "self"). 
        If model name ends with an integer range symbol [n:m], all models 
        matching the pattern name:<k> where <k> is an integer given by 
        range(n,m) will be coupled to the source. 
        WARNING: In python, a one-element tuples (aka singleton) MUST end
        with a comma: (1,) is a tuple, but (1) is just identical to 1.
        """
        raise NotImplementedError()

    def selectSpecs(self):
        raise NotImplementedError()


class ClassicDevsCoupledSimulator(ClassicDevsAbstractSimulator):
    __active_children = None
    __children = None

    def __init__(self, parent, model):
        self.__active_children = []
        self.__children = dict()
        super().__init__(parent,model)

    @invalid_attribute
    def _active_children(self):
        pass

    @invalid_attribute
    def _children(self):
        pass

    def getChildren(self):
        return self.__children

    def build(self):
        """
        Recursiveley create simulators for submodels and
        initialize them.
        """
        #print("{}.build()".format(self))
        for mname,model in self.getModel().getSubModels().items():
            #print("{}.build : building {}({})".format(self,model,mname))
            if issubclass(model.__class__,ClassicDevsCoupledModel):
                sim = ClassicDevsCoupledSimulator(self,model)
                sim.build()
            else:
                sim = ClassicDevsAtomicSimulator(self,model)
            self.__children[mname]=sim


    def findImminents(self,time):
        if time != self.getTimeNext():
            imminents = []
        else:
            imminents = [s for s in filter((lambda x: x.getTimeNext() == time), self.__children.values())]
        return imminents

    def activate(self):
        super().activate()
        #for sim in self.__active_children:
        #    sim.activate()

    def onINIT(self,mfrom,mtime,param):
        for sim in self.__children.values():
            sim.queue_msg(InitMsg(self,mtime))
            self.__active_children.append(sim)
            sim.activate()

    def onSTAR(self,mfrom,mtime,param):
        if mtime != self.getTimeNext(): 
            # I think this is an error: if this happens, we dont notify the parent
            # that we are done
            raise Exception('Star message requested at a time that is not reached yet!')
        imminents = self.findImminents(mtime)
        #print("{}.onSTAR(from={}, mtime={}, param={}) ; imminents = {}".format(self,mfrom,mtime,param,imminents))
        if len(imminents) == 1:
            winner = imminents[0]
        else:
            this_set = set((i.getModel().getName() for i in imminents))
            winner_name = self.getModel().select(this_set)
            if not winner_name in this_set:
                raise TypeError("Select returned a winner that is not in the set of candidates!")
            if not winner_name:
                raise Exception('Select was not able to find a winner among {}'.format(this_set))
            winner = self.__children[winner_name]
        winner.queue_msg(StarMsg(self,mtime))
        self.__active_children.append(winner)
        winner.activate()

    def onIN(self,mfrom,mtime,param):
        if not (self.getTimeLast() <= mtime <= self.getTimeNext()):
            raise Exception('In message requested at wrong time')
        # find all submodels in EIC
        for eic_name in self.getModel().getCouplings()['self']:
            sim = self.__children[eic_name]
            # TODO: missing Z conversion to send Z(param)
            sim.queue_msg(InMsg(self,mtime,param))
            self.__active_children.append(sim)
            sim.activate()

    def onOUT(self,mfrom,mtime,param):
        if param[0] is None:
            #print("{}.onOUT: ignoring None message from {}".format(self,mfrom))
            return
        for mname in self.getModel().getCouplings()[mfrom.getModel().getName()]:
            if mname == 'self':
                self.getParent().queue_msg(OutMsg(self,mtime,param))
            else:
                sim = self.__children[mname]
                sim.queue_msg(InMsg(mfrom,mtime,param))
                self.__active_children.append(sim)
                sim.activate()

    def onDONE(self,mfrom,mtime,param):
        #print("{}.onDONE(from={}, time={}): stil active={}".format(self,mfrom,mtime,self.__active_children))
        self.__active_children.remove(mfrom)
        if len(self.__active_children) == 0:
            children = tuple(self.__children.values())
            last = children[0].getTimeLast()
            next = children[0].getTimeNext()
            self.updateTimes(last,next)
            if len(children) > 1:
                for c in children[1:]:
                    last = max(self.getTimeLast(),c.getTimeLast())
                    next = min(self.getTimeNext(),c.getTimeNext())
                    self.updateTimes(last,next)
            #print("onDone: set time_last={}, time_next={}".format(self.getTimeLast(),self.getTimeNext()))
            #print("{}.onDONE(): queueing DoneMsg upward on parent={}".format(self,self.getParent()))
            self.getParent().queue_msg(DoneMsg(self,self.getTimeNext()))


    def __repr__(self):
        return "{}({})".format(self.__class__.__name__, self.getModel())

class ClassicDevsRootCoordinator(ClassicDevsAbstractSimulator):
    __endtime = None
    __simulator = None


    def __init__(self,endtime,rootmodel):
        self.__endtime = endtime
        (mmod,mtype,mname,args) = rootmodel
        model = self.createRootModel(mmod,mtype,mname,args)
        super().__init__(self,model)
        self.__simulator = self.createRootSim(model)
        self.__simulator.build()
        #self.build()
        self.updateTimes(-1,0)



    def createRootModel(self,mmod,mtype,mname,args):
        instance_name = mtype+'("'+mname+'"'
        if args: instance_name += ','+args
        instance_name += ')'
        exec('from '+mmod+' import '+mtype)
        model=None
        model=eval(instance_name)
        if not issubclass(model.__class__,Model):
            raise TypeError("Unable to create model: Invalid model type ("+mtype+")")
        model.build('')
        return model

    def createRootSim(self,model):
        if issubclass(model.__class__,ClassicDevsCoupledModel):
            sim = ClassicDevsCoupledSimulator(self,model)
        else:
            sim = ClassicDevsAtomicSimulator(self,model)
        return sim

    def start(self):
        #print ("------------RootSim={}, RootSim.simulator={}".format(self,self.__simulator))
        #self.__simulator.queue_msg(InitMsg(self,0))
        self.__simulator.queue_msg(InitMsg(self,0))
        self.__simulator.activate()
        #print("time_last={} endtime={}".format(self.getTimeLast(),self.__endtime))
        #counter=0
        while not self.getTimeLast() >= self.__endtime:
            #print ("Root: calling activate()")
            self.__simulator.activate()
            self.activate()
            #print("----------- ROOT looping: time_last={} time_next={} endtime={}".format(self.getTimeLast(),self.getTimeNext(), self.__endtime))
            #counter+=1

    def onDONE(self,mfrom,mtime,param):
        self.updateTimes(self.getTimeNext(), mtime)
        self.__simulator.queue_msg(StarMsg(self,mtime))
        self.__simulator.activate()
        #self.queue_msg(StarMsg(self,mtime))
        #self.activate()

    def onOUT(self,mfrom,mtime,param):
        print("Root: output={}".format(param))

    def __str__(self):
        return "RootCoord"

if __name__ == "__main__":
    help('classic_devs')