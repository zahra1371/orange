/*
    This file is part of Orange.

    Orange is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.

    Orange is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with Orange; if not, write to the Free Software
    Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

    Authors: Janez Demsar, Blaz Zupan, 1996--2002
    Contact: janez.demsar@fri.uni-lj.si
*/


#ifndef __SPEC_GEN_HPP
#define __SPEC_GEN_HPP

#include "orvector.hpp"
#include "examplegen.hpp"
#include "filter.hpp"
#include "contingency.hpp"

WRAPPER(Filter);
WRAPPER(RandomGenerator);

/*  A base for 'filter generators' i.e. generators, which can be put on top of other generator and modify its
    examples (usualy skip or add examples...). The behaviour of the generator is modified by overriding iterator
    handling method (usualy begin and increaseIterator). */
class TAdapterGenerator : public TExampleGenerator {
public:
  __REGISTER_CLASS

  /*  Iterators, pointing to the first and the one-beyond-the-last example from the underlying generator.
      They are not necessarily equal to gen->begin() and gen->end() so the TAdapterGenerator can be used to
      select a set of consecutive examples of underlying generator. */
  TExampleIterator first, last;

  TAdapterGenerator(PDomain, const TExampleIterator &first, const TExampleIterator &last);
  TAdapterGenerator(PDomain, PExampleGenerator);
  TAdapterGenerator(PExampleGenerator);

  int traverse(visitproc visit, void *arg);
  int dropReferences();

  virtual TExampleIterator begin();
  virtual TExampleIterator begin(void *derData);
  virtual bool randomExample(TExample &);

  virtual int numberOfExamples();

  virtual void increaseIterator(TExampleIterator &);
  virtual bool sameIterators(const TExampleIterator &, const TExampleIterator &);
  virtual void deleteIterator(TExampleIterator &);
  virtual void copyIterator(const TExampleIterator &, TExampleIterator &);
};


class TAdapterIteratorData {
public:
  TExampleIterator subIterator;
  void *data;

  TAdapterIteratorData(const TExampleIterator &, void * =NULL);
};

/*  Derived from TAdapterGenerator, this class overrides the begin() and increaseIterator(void *) methods to
    skip the examples which are not accepted by the given filter. */
class TFilteredGenerator : public TAdapterGenerator {
public:
  __REGISTER_CLASS

  PFilter filter; //P decides which examples are skipped
  
  TFilteredGenerator(PFilter, PDomain, const TExampleIterator &, const TExampleIterator &);
  TFilteredGenerator(PFilter, PExampleGenerator);

  virtual TExampleIterator begin();
  virtual void increaseIterator(TExampleIterator &);
};


WRAPPER(EFMDataDescription)


/*  Changes the example someway by redefining begin and increaseIterator to call an abstract
    method changeExample */
class TChangeExampleGenerator : public TAdapterGenerator {
public:
  __REGISTER_ABSTRACT_CLASS

  TChangeExampleGenerator(PDomain, const TExampleIterator &, const TExampleIterator &);
  TChangeExampleGenerator(PExampleGenerator);

  virtual TExampleIterator begin();
  virtual void increaseIterator(TExampleIterator &);

  virtual TExampleIterator changeExample(const TExampleIterator &)=0;
};


/*  Derived from TChangeExampleGenerator, TMissValuesGenerator replaces values of certain
    attributes (given the probability for change) with DK or DC */
class TMissValuesGenerator : public TChangeExampleGenerator {
public:
  __REGISTER_CLASS

  PFloatList replaceProbabilities; //P probabilities for replacing attributes' values
  PRandomGenerator randomGenerator; //P random generator

  TMissValuesGenerator(const vector<float> &, PDomain &, TExampleIterator &, TExampleIterator &);
  TMissValuesGenerator::TMissValuesGenerator(const vector<float> &, PExampleGenerator);

  TExampleIterator changeExample(const TExampleIterator &it);
};


class TNoiseValuesGenerator : public TChangeExampleGenerator {
public:
  __REGISTER_CLASS

  PFloatList replaceProbabilities; //P probabilities for replacing attributes' values
  PRandomGenerator randomGenerator; //P random generator

  TNoiseValuesGenerator(const vector<float> &, PDomain &, TExampleIterator &, TExampleIterator &);
  TNoiseValuesGenerator(const vector<float> &, PExampleGenerator);

  TExampleIterator changeExample(const TExampleIterator &it);
};


class TGaussianNoiseGenerator : public TChangeExampleGenerator {
public:
  __REGISTER_CLASS

  PFloatList deviations; //P deviations for attributes' values
  PRandomGenerator randomGenerator; //P random generator

  TGaussianNoiseGenerator(const vector<float> &, PDomain &, TExampleIterator &, TExampleIterator &);
  TGaussianNoiseGenerator(const vector<float> &, PExampleGenerator);

  TExampleIterator changeExample(const TExampleIterator &it);
};

#endif
