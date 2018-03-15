

# YapDEVS

YapDEVS is Yet Another Python DEVS simulator.


This module provides the elements for building Classic DEVS models
(with ports) simulations. It is mostly meant for educational purpose
and, therefore, should not be relied on for complex simulations.


## INSTALL

This python module requires python version 3.5 or higher.
In case this version is not already installed and you do NOT have admin permissions, you can still install the latest version of python using [pyenv](https://github.com/pyenv/pyenv). For example as follows on Ubuntu (see also instructions on [pyenv](https://github.com/pyenv/pyenv) page):

```
$ git clone https://github.com/pyenv/pyenv.git ~/.pyenv
$ echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.bashrc
$ echo 'export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.bashrc
$ echo -e 'if command -v pyenv 1>/dev/null 2>&1; then\n  eval "$(pyenv init -)"\nfi' >> ~/.bashrc
$ source ~/.bashrc
```


Then install the desired python version, eg. 3.6.4:

```
$ pyenv install 3.6.4
```


## TRY IT

To provided example is composed of 3 Classic DEVS models:
- a generator atomic model
- a processor atomic model
- a couped model on which the generator is connected to the processor and the
output of the processor to the output of coupled model

To try it, simply run the following shell command

```
$ python3 procgen.py
```



To run the simulation, first create an instance of root coordinator with two paramters: the temrination time and the root coupled model (defined by a tuple `(module, class, name, params)`):

```python
rc = ClassicDevsRootCoordinator(50.0,('procgen','CoupledGenerator','coupled',None))
```


The trace produced is configured using the  `setTraceFuncs` method call (to be soon documented). For example imn the following we trace all the traceable events in all the model hierarchy, with 9 and 20 space alignments:

```python
setTraceFuncs('*','*',rc,9,20)
```


Then run the simulation by sending a start message to root coordinator:

```python
rc.start()
```


The simulation terminates when time specified as a parameter to the root coordinator instance is reached.


## QUICK MANUAL


According to the specification, Classic DEVS models can be defined 
either as coupled or atomic models.

Atomic models must extend the `ClassicDevsAtomicModel` class and coupled
models must extend the `ClassicDevsCoupledModel` according to the following
rules.

### Atomic Models


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

## Coupled Models


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

- `couplingsSpecs` : returns a sequence (list or tuple) of pairs
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