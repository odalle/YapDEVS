

traceFuncs=dict()
trace_pwidth = 17
trace_swidth = 9
root_coord = None

def setTraceFuncs(funcs,paths,rcoord, swidth=9, spwidth=17):
    global traceFuncs,trace_swidth, trace_pwidth, root_coord
    trace_swidth, trace_pwidth, root_coord = swidth, spwidth, rcoord
    for path in paths:
        #print("Setting traceFuncs={}".format(funcs) )
        traceFuncs[path] = funcs

class Error(Exception):
    """Base class for exceptions in this module."""
    pass

class ImplementationError(Error):
    """Exception raised when some assertion fails due to an implementation error.

    Attributes:
        - instance:     object instance
        - message:      error message
    """
    def __init__(self,instance,message):
        self.instance = instance
        self.message  = message

def invalid_attribute(func):

    def wrapper(*args):
        raise ImplementationError(args[0],'Using attribute {}'.format(func.__name__))

    return wrapper

def shrink_str(max_size, string):
        if len(string) > max_size:
            return '...'+string[-max_size+3:]
        return string

def trace_transition(tag):
    """ 
    Parameterized decorator annotation for producing traces 
    when external or internal transitions occur.

    @parameter tag used to distinguish between external 
    and internal transitions
    @parameter pwidth maximum width for the component path width.
    @parameter swidth maximum width for the state name
    """
    

    def decorator(func):
        global traceFuncs, trace_pwidth, trace_swidth

        def wrapper(*args):
            # TraceFuncs is a dict with path names as keys and func names as values
            if not '*' in traceFuncs.get(args[0].getPath(),()) \
                and not func.__name__ in traceFuncs.get(args[0].getPath(),()) \
                and not '*' in traceFuncs.get('*',()) \
                and not func.__name__ in traceFuncs.get('*',()):
                return func(*args)
            in_evt = ''
            old_state = args[0].getPhase()
            if old_state is None:
                old_state = "None"
            res=func(*args)
            output = str(res)
            if func.__name__ in ('onExternal', 'onInternal', 'onOut'):
                if res is True:
                    output = '(cont)'
                else:
                    output=res[0]             
            if func.__name__ in ('onExternal' ):
                in_evt = ' in='+str(tuple(map(lambda s: s[0], args[4])))
            print("tl:{Last} tn:{Next} {Path:{Pwidth}}{Tag}({Old:{Swidth}}) -> {New:{Swidth}}{Evt}".format(Last=root_coord.getTimeLast(),Next=root_coord.getTimeNext(), Tag=tag, Pwidth=trace_pwidth, Path=shrink_str(trace_pwidth,args[0].getPath()),Evt=in_evt, Old=old_state,New=output,Swidth=trace_swidth))
            return res
        return wrapper
    return decorator

def trace_select(func):

    def wrapper(*args):

        res = func(*args)
        print("tl:{Last} tn:{Next} {Path:{Pwidth}}slct({Padding}) -> {Candidates} : {Winner}".format(Last=root_coord.getTimeLast(),Next=root_coord.getTimeNext(), Pwidth=trace_pwidth,Path=shrink_str(trace_pwidth,args[0].getPath()),Candidates=args[1],Winner=res,Padding='.'* trace_swidth))
        return res
    return wrapper

class TraceDict(dict):

    def setPath(self,path):
        self.owner_path = path

    def __setitem__(self,index,value):
        if '*' in traceFuncs.get(self.owner_path,()) \
                or index in traceFuncs.get(self.owner_path,()) \
                or '*' in traceFuncs.get('*',()) \
                or index in traceFuncs.get('*',()):
            print("tl:{Last} tn:{Next} {Path:{Pwidth}} set({Index:{Swidth}}) -> {Value}".format(Last=root_coord.getTimeLast(),Next=root_coord.getTimeNext(), Pwidth=trace_pwidth,Path=shrink_str(trace_pwidth,self.owner_path),Value=value, Index=index, Swidth=trace_swidth))
        super().__setitem__(index,value)


