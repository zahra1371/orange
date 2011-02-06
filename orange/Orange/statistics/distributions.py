"""

Orange has several classes for computing and storing basic statistics about
features, distributions and contingencies.

    
========================================
Basic Statistics for Continuous Features
========================================

The are two simple classes for computing basic statistics
for continuous features, such as their minimal and maximal value
or average: :class:`BasicStatistics` holds the statistics for a single feature
and :class:`DomainBasicStatistics` is a container storing a list of instances of
the above class for all features in the domain.

.. class:: BasicStatistics

    `DomainBasicStatistics` computes on-the fly statistics. 

    .. attribute:: variable
    
        The descriptor for the feature to which the data applies.

    .. attribute:: min, max

        Minimal and maximal feature value encountered
        in the data table.

    .. attribute:: avg, dev

        Average value and standard deviation.

    .. attribute:: n

        Number of instances for which the value was defined
        (and used in the statistics). If instances were weighted,
        ``n`` is the sum of weights of those instances.

    .. attribute:: sum, sum2

        Weighted sum of values and weighted sum of
        squared values of this feature.

    ..
        .. attribute:: holdRecomputation
    
            Holds recomputation of the average and standard deviation.

    .. method:: add(value[, weight=1])
    
        :param value: Value to be added to the statistics
        :type value: float
        :param weight: Weight assigned to the value
        :type weight: float

        Adds a value to the statistics.

    ..
        .. method:: recompute()

            Recomputes the average and deviation.

    The class works as follows. Values are added by :obj:`add`, for each value
    it checks and, if necessary, adjusts :obj:`min` and :obj:`max`, adds the value to
    :obj:`sum` and its square to :obj:`sum2`. The weight is added to :obj:`n`.


    The statistics does not include the median or any other statistics that can be computed on the fly, without remembering the data. Quantiles can be computed
    by :obj:`ContDistribution`. !!!TODO

    Instances of this class are seldom constructed manually; they are more often
    returned by :obj:`DomainBasicStatistics` described below.

.. class:: DomainBasicStatistics

    ``DomainBasicStatistics`` behaves like a ordinary list, except that its
    elements can also be indexed by feature descriptors or feature names.

    .. method:: __init__(data[, weight=None])

        :param data: A table of instances
        :type data: Orange.data.Table
        :param weight: The id of the meta-attribute with weights
        :type weight: `int` or none
        
        Constructor computes the statistics for all continuous features in the
        give data, and puts `None` to the places corresponding to other types of
        features.
    
    .. method:: purge()
    
        Removes the ``None``'s corresponding to non-continuous features.
    
    part of `distributions-basic-stat.py`_ (uses monks-1.tab)
    
    .. literalinclude:: code/distributions-basic-stat.py
        :lines: 1-10

    Output::

             feature   min   max   avg
        sepal length 4.300 7.900 5.843
         sepal width 2.000 4.400 3.054
        petal length 1.000 6.900 3.759
         petal width 0.100 2.500 1.199


    part of `distributions-basic-stat`_ (uses iris.tab)
    
    .. literalinclude:: code/distributions-basic-stat.py
        :lines: 11-

    Output::

        5.84333467484 

.. _distributions-basic-stat: code/distributions-basic-stat.py
.. _distributions-basic-stat.py: code/distributions-basic-stat.py


Contingency Matrix
==================

Contingency matrix contains conditional distributions. When initialized, they
will typically contain absolute frequencies, that is, the number of instances
with a particular combination of two variables' values. If they are normalized
by dividing each cell by the row sum, the represent conditional probabilities
of the column variable (here denoted as ``innerVariable``) conditioned by the
row variable (``outerVariable``). 

Contingencies work with both, discrete and continuous variables.

.. _distributions-contingency: code/distributions-contingency.py

part of `distributions-contingency`_ (uses monks-1.tab)

.. literalinclude:: code/distributions-contingency.py
    :lines: 1-8

This code prints out::

    1 <0.000, 108.000>
    2 <72.000, 36.000>
    3 <72.000, 36.000>
    4 <72.000, 36.000> 

Contingencies behave like lists of distributions (in this case, class distributions) indexed by values (of `e`, in this example). Distributions are, in turn indexed
by values (class values, here). The variable `e` from the above example is called
the outer variable, and the class is the inner. This can also be reversed, and it
is also possible to use features for both, outer and inner variable, so the
matrix shows distributions of one variable's values given the value of another.
There is a corresponding hierarchy of classes for handling hierarchies: :obj:`Contingency` is a base class for :obj:`ContingencyVarVar` (both variables
are attribtes) and :obj:`ContingencyClass` (one variable is the class).
The latter is the base class for :obj:`ContingencyVarClass` and :obj:`ContingencyClassVar`.

The most commonly used of the above classes is :obj:`ContingencyVarClass` which
can compute and store conditional probabilities of classes given the feature value.

.. class:: Orange.statistics.distribution.Contingency

    .. attribute:: outerVariable

       Descriptor (:class:`Orange.data.feature.Feature`) of the outer variable.

    .. attribute:: innerVariable

        Descriptor (:class:`Orange.data.feature.Feature`) of the inner variable.
 
    .. attribute:: outerDistribution

        The marginal distribution (:class:`Distribution`) of the outer variable.

    .. attribute:: innerDistribution

        The marginal distribution (:class:`Distribution`) of the inner variable.
        
    .. attribute:: innerDistributionUnknown

        The distribution (:class:`Distribution`) of the inner variable for 
        instances for which the outer variable was undefined.
        This is the difference between the ``innerDistribution``
        and unconditional distribution of inner variable.
      
    .. attribute:: varType

        The type of the outer feature (:obj:`Orange.data.Type`, usually
        :obj:`Orange.data.feature.Discrete` or 
        :obj:`Orange.data.feature.Continuous`). ``varType`` equals ``outerVariable.varType`` and ``outerDistribution.varType``.

    .. method:: __init__(outerVariable, innerVariable)
     
        :param outerVariable: Descriptor of the outer variable
        :type outerVariable: Orange.data.feature.Feature
        :param outerVariable: Descriptor of the inner variable
        :type innerVariable: Orange.data.feature.Feature
        
        Construct an instance of ``Contingency``.
     
    .. method:: add(outer_value, inner_value[, weight=1])
    
        :param outer_value: The value for the outer variable
        :type outer_value: int, float, string or :obj:`Orange.data.Value`
        :param inner_value: The value for the inner variable
        :type inner_value: int, float, string or :obj:`Orange.data.Value`
        :param weight: Instance weight
        :type weight: float

        Add an element to the contingency matrix by adding
        ``weight`` to the corresponding cell.

    .. method:: normalize()

        Normalize all distributions (rows) in the contingency to sum to ``1``::
        
            >>> cont.normalize()
            >>> for val, dist in cont.items():
                   print val, dist

        Output: ::

            1 <0.000, 1.000>
            2 <0.667, 0.333>
            3 <0.667, 0.333>
            4 <0.667, 0.333>

        .. note::
       
            This method doesn't change the ``innerDistribution`` or
            ``outerDistribution``.
        
    With respect to indexing, contingency matrix is a cross between dictionary
    and a list. It supports standard dictionary methods ``keys``, ``values`` and
    ``items``.::

        >> print cont.keys()
        ['1', '2', '3', '4']
        >>> print cont.values()
        [<0.000, 108.000>, <72.000, 36.000>, <72.000, 36.000>, <72.000, 36.000>]
        >>> print cont.items()
        [('1', <0.000, 108.000>), ('2', <72.000, 36.000>),
        ('3', <72.000, 36.000>), ('4', <72.000, 36.000>)] 

    Although keys returned by the above functions are strings, contingency
    can be indexed with anything that converts into values
    of the outer variable: strings, numbers or instances of ``Orange.data.Value``.::

        >>> print cont[0]
        <0.000, 108.000>
        >>> print cont["1"]
        <0.000, 108.000>
        >>> print cont[orange.Value(data.domain["e"], "1")] 

    The length of ``Contingency`` equals the number of values of the outer
    variable. However, iterating through contingency
    doesn't return keys, as with dictionaries, but distributions.::

        >>> for i in cont:
            ... print i
        <0.000, 108.000>
        <72.000, 36.000>
        <72.000, 36.000>
        <72.000, 36.000>
        <72.000, 36.000> 


.. class:: Orange.statistics.distribution.ContingencyClass

    ``ContingencyClass`` is an abstract base class for contingency matrices
    that contain the class, either as the inner or the outer
    variable.

    .. attribute:: classVar (read only)
    
        The class attribute descriptor.
        This is always equal either to :obj:`Contingency.innerVariable` or
        ``outerVariable``.

    .. attribute:: variable
    
        The class attribute descriptor.
        This is always equal either to innerVariable or outerVariable

    .. method:: add_attrclass(attribute_value, class_value[, weight])

        Adds an element to contingency. The difference between this and
        Contigency.add is that the feature value is always the first
        argument and class value the second, regardless whether the feature
        is actually the outer variable or the inner. 



.. class:: Orange.statistics.distribution.ContingencyClass

    ContingencyAttrClass is derived from ContingencyClass.
    Here, feature is the outer variable (hence variable=outerVariable)
    and class is the inner (classVar=innerVariable), so this form of
    contingency matrix is suitable for computing the conditional probabilities
    of classes given a value of a feature.

    Calling add_attrclass(v, c) is here equivalent to calling add(v, c).
    In addition to this, the class supports computation of contingency from instances,
    as you have already seen in the example at the top of this page.


    .. method:: ContingencyAttrClass(feature, class_attribute)

        The inherited constructor, which does exactly the same
        as Contingency's constructor.

    .. method:: ContingencyAttrClass(feaure, class_attribute)

        The inherited constructor, which does exactly the same
        as Contingency's constructor.

    .. method::  ContingencyAttrClass(feature, instances[, weightID])

        Constructor that constructs the contingency and computes the
        data from the given instances. If these are weighted, the meta
        attribute with instance weights can be specified.     

    .. method:: p_class(attribute_value)

        Returns the distribution of classes given the attribute_value.
        If the matrix is normalized, this is equivalent to returning
        self[attribute_value].
        Result is returned as a normalized Distribution.

    .. method:: p_class(attribute_value, class_value)

        Returns the conditional probability of class_value given the
        attribute_value. If the matrix is normalized, this is equivalent
        to returning self[attribute_value][class_value].

Don't confuse the order of arguments: feature value is the first,
class value is the second, just as in add_attrclass. Although in this
instance counterintuitive (since the returned value represents the conditional
probability P(class_value|attribute_value), this order is uniform for all
(applicable) methods of classes derived from ContingencyClass.

You have seen this form of matrix used already at the top of the page.
We shall only explore the new stuff we've learned about it.


.. _distributions-contingency3.py: code/distributions-contingency3.py

part of `distributions-contingency3.py`_ (uses monks-1.tab)

.. literalinclude:: code/distributions-contingency3.py
    :lines: 1-25

The inner and the outer variable and their relations to the class
and the features are as expected.::

    Inner variable:  y
    Outer variable:  e

    Class variable:  y
    Feature:         e

Distributions are normalized and probabilities are elements from the
normalized distributions. Knowing that the target concept is
y := (e=1) or (a=b), distributions are as expected: when e equals 1, class 1
has a 100% probability, while for the rest, probability is one third, which
agrees with a probability that two three-valued independent features
have the same value.::

    Distributions:
      p(.|1) = <0.000, 1.000>
      p(.|2) = <0.662, 0.338>
      p(.|3) = <0.659, 0.341>
      p(.|4) = <0.669, 0.331>

    Probabilities of class '1'
      p(1|1) = 1.000
      p(1|2) = 0.338
      p(1|3) = 0.341
      p(1|4) = 0.331

    Distributions from a matrix computed manually:
      p(.|1) = <0.000, 1.000>
      p(.|2) = <0.662, 0.338>
      p(.|3) = <0.659, 0.341>
      p(.|4) = <0.669, 0.331>


Manual computation using add_attrclass is similar
(to be precise: exactly the same) as computation using add.

.. _distributions-contingency3.py: code/distributions-contingency3.py

part of `distributions-contingency3.py`_ (uses monks-1.tab)

.. literalinclude:: code/distributions-contingency3.py
    :lines: 27-


.. class:: Orange.statistics.distribution.ContingencyClassAttr

    ContingencyClassAttr is similar to ContingencyAttrClass except that here
    the class is the outer and the feature the inner variable.
    As a consequence, this form of contingency matrix is suitable
    for computing conditional probabilities of feature values given class.
    Constructor and add_attrclass nevertheless get the arguments
    in the same order as for ContingencyAttrClass, that is,
    feaure first, class second.


    ..method:: ContingencyClassAttr(attribute, class_attribute)

        The inherited constructor is exactly the same as Contingency's
        constructor, except that the argument order is reversed
        (in Contingency, the outer attribute is given first,
        while here the first argument, attribute, is the inner attribute).
    
    .. method:: ContingencyAttrClass(attribute, examples[, weightID])

        Constructs the contingency and computes the data from the given
        examples. If these are weighted, the meta attribute with example
        weights can be specified. 
    
    .. method:: p_attr(class_value)

        Returns the distribution of attribute values given the class_value.
        If the matrix is normalized, this is equivalent to returning
        self[class_value]. Result is returned as a normalized Distribution.

    .. method:: p_attr(attribute_value, class_value)
    
        Returns the conditional probability of attribute_value given the
        class_value. If the matrix is normalized, this is equivalent to
        returning self[class_value][attribute_value].
  
As you can see, the class is rather similar to ContingencyAttrClass,
except that it has p_attr instead of p_class.
If you, for instance, take the above script and replace the class name,
the first bunch of prints print out


.. _distributions-contingency4.py: code/distributions-contingency4.py

part of the output from `distributions-contingency4.py`_ (uses monk1.tab)

The inner and the outer variable and their relations to the class
and the features are as expected.::

    Inner variable:  e
    Outer variable:  y

    Class variable:  y
    Feature:         e


This is exactly the reverse of the printout from ContingencyAttrClass.
To print out the distributions, the only difference now is that you need
to iterate through values of the class attribute and call p_attr. For instance,

part of `distributions-contingency4.py`_ (uses monks-1.tab)

.. literalinclude:: code/distributions-contingency4.py
    :lines: 31-

will print::
    p(.|0) = <0.000, 0.333, 0.333, 0.333>
    p(.|1) = <0.500, 0.167, 0.167, 0.167>


If the class value is '0', then attribute e cannot be '1' (the first value),
but can be anything else, with equal probabilities of 0.333.
If the class value is '1', e is '1' in exactly half of examples
(work-out why this is so); in the remaining cases,
e is again distributed uniformly.
    

.. class:: Orange.statistics.distribution.ContingencyAttrAttr

    ContingencyAttrAttr stores contingency matrices in which none
    of the features is the class. This is rather similar to Contingency,
    except that it has an additional constructor and method for getting
    the conditional probabilities.

    .. method:: ContingencyAttrAttr(outer_variable, inner_variable)

        This constructor is exactly the same as that of Contingency.

    .. method:: ContingencyAttrAttr(outer_variable, inner_variable,  instances[, weightID])

        Computes the contingency from the given instances.

    .. method:: p_attr(outer_value)

        Returns the probability distribution of the inner
        variable given the outer variable.

    .. method:: p_attr(outer_value, inner_value)

        Returns the conditional probability of the inner_value
        given the outer_value.


In the following example, we shall use the ContingencyAttrAttr
on dataset "bridges" to determine which material is used for
bridges of different lengths.


.. _distributions-contingency5: code/distributions-contingency5.py

part of `distributions-contingency5`_ (uses bridges.tab)

.. literalinclude:: code/distributions-contingency5.py
    :lines: 1-19

The output tells us that short bridges are mostly wooden or iron,
and the longer (and the most of middle sized) are made from steel.::

    SHORT:
       WOOD (56%)
       IRON (44%)

    MEDIUM:
       WOOD (9%)
       IRON (11%)
       STEEL (79%)

    LONG:
       STEEL (100%)

As all other contingency matrices, this one can also be computed "manually".

.. literalinclude:: code/distributions-contingency5.py
    :lines: 20-


====================================
Contingencies with Continuous Values
====================================

What happens if one or both features are continuous?
As first, contingencies can be built for such features as well.
Just imagine a contingency as a dictionary with features values
as keys and objects of type Distribution as values.

If the outer feature is continuous, you can use either its values
or ordinary floating point number for indexing. The index must be one
of the values that do exist in the contingency matrix.

The following script will query for a distribution in between
the first two keys, which triggers an exception.


.. _distributions-contingency6: code/distributions-contingency6.py

part of `distributions-contingency6`_ (uses monks-1.tab)

.. literalinclude:: code/distributions-contingency6.py
    :lines: 1-5,18,19

If you still find such contingencies useful, you need to take care
about what you pass for indices. Always use the values from keys()
directly, instead of manually entering the keys' values you see printed.
If, for instance, you print out the first key, see it's 4.500 and then
request cont[4.500] this can give an index error due to rounding.

Contingencies with continuous inner features are more useful.
As first, indexing by discrete values is easier than with continuous.
Secondly, class Distribution covers both, discrete and continuous
distributions, so even the methods p_class and p_attr will work,
except they won't return is not the probability but the density
(interpolated, if necessary). See the page about Distribution
for more information.

For instance, if you build a ContingencyClassAttr on the iris dataset,
you can enquire about the probability of the sepal length 5.5.

.. _distributions-contingency7: code/distributions-contingency7.py

part of `distributions-contingency7`_ (uses iris.tab)

.. literalinclude:: code/distributions-contingency7.py

    
The script's output is::

    Estimated frequencies for e=5.5
      f(5.5|Iris-setosa) = 2.000
      f(5.5|Iris-versicolor) = 5.000
      f(5.5|Iris-virginica) = 1.000


========================================
Computing Contingencies for All Features
========================================

Computing contingency matrices requires iteration through instances.
We often need to compute ContingencyAttrClass or ContingencyClassAttr
for all features in the dataset and it is obvious that this will be faster
if we do it for all features at once. That's taken care of
by class DomainContingency.

DomainContingency is basically a list of contingencies,
either of type ContingencyAttrClass or ContingencyClassAttr, with two
additional fields and a constructor that computes the contingencies.

.. class:: DomainContingency(instances[, weightID][, classIsOuter=0|1])

    Constructor needs to be given a list of instances.
    It constructs a list of contingencies; if classIsOuter is 0 (default),
    these will be ContingencyAttrClass, if 1, ContingencyClassAttr are used.
    It then iterates through instances and computes the contingencies.

    .. attribute:: classIsOuter (read only)

        Tells whether the class is the outer or the inner featue.
        Effectively, this tells whether the elements of the list
        are ContingencyAttrClass or ContingencyClassAttr.

    .. attribute:: classes

        Contains the distribution of class values on the entire dataset.

    .. method:: normalize

        Calls normalize for each contingency.

The following script will print the contingencies for features
"a", "b" and "e" for the dataset Monk 1.

.. _distributions-contingency8: code/distributions-contingency8.py

part of `distributions-contingency8`_ (uses monks-1.tab)

.. literalinclude:: code/distributions-contingency8.py
    :lines: 1-11


The contingencies in the DomainContingency dc are of type ContingencyAttrClass
and tell us conditional distributions of classes, given the value of the feature.
To compute the distribution of feature values given the class,
one needs to get a list of ContingencyClassAttr.

Note that classIsOuter cannot be given as positional argument,
but needs to be passed by keyword.

.. _distributions-contingency8: code/distributions-contingency8.py

part of `distributions-contingency8`_ (uses monks-1.tab)

.. literalinclude:: code/distributions-contingency8.py
    :lines: 13- 

"""



from Orange.core import \
     DomainContingency, \
     DomainDistributions, \
     DistributionList, \
     ComputeDomainContingency, \
     Contingency

from Orange.core import BasicAttrStat as BasicStatistics
from Orange.core import DomainBasicAttrStat as DomainBasicStatistics
from Orange.core import ContingencyAttrAttr as ContingencyVarVar
from Orange.core import ContingencyAttrAttr as ContingencyClass
from Orange.core import ContingencyAttrAttr as ContingencyVarClass
from Orange.core import ContingencyAttrAttr as ContingencyClassVar
