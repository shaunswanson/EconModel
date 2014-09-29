'''
Small business lifecycle modeling based on individual consumer needs

Written by Dan Morris. 9/27/14 -

Overview:
  We create a city which contains people and small businesses. People generate
    needs each cycle and go to nearby businesses to fulfill those needs. If a
    person cannot find a business close by to fulfill their needs, those needs
    accumulate and their search radius expands. Businesses spend cash each
    cycle, and must take in enough revenue to stay afloat. If a business's cash
    drops below zero, that business dies and can be replaced by a new startup.

  Each cycle represents approximately one earth-week.

Objects:
  City
  Person
  Business
  BusinessLocation
  BusinessType
  DemandType

Helper Files:
  functions.py - contains non-object functions
  business_types.json - contains reference of business types
  demand_types.json - contains reference of demand types
'''

import numpy as np
from scipy.stats import poisson, norm
from random import sample, choice
import functions as f

class City(object):
  def __init__(self, name, size, n_people):
    self.name = name
    self.size = float(size) # radius of the city
    self.age = 0 # number of cycles

    self.dtypes = self.compile_dtypes()
    self.btypes = self.compile_btypes()
    self.people = []
    self.populate(n_people)
    self.businesses = []
    self.business_locations = self.generate_business_locations()
    self.business_populate(ratio = .75)
    self.failed_businesses = []

  def compile_dtypes(self):
    dtraw = f.get_demand_types() # dict of demand types from json
    dt = {}
    for t in dtraw:
      dt[t] = DemandType(t, dtraw[t]['dlambda'], dtraw[t]['dprice'])
    return dt

  def compile_btypes(self):
    btraw = f.get_business_types()
    bt = {}
    for t in btraw:
      bt[t] = BusinessType(t, btraw['init_cash'], btraw['init_need_threshold'],
                           btraw['init_need_radius'], btraw['burnrate'])
    return bt

  def populate(self, n):
    '''
    Adds n people to the city
    '''
    for i in range(n):
      self.population.append(Person(self, f.generate_person_name()))

  def generate_business_locations(self):
    '''
    Simplified: Create a business location at every (int, int) location in
      the city limits.
    '''
    bl = []
    for x in range(-int(self.size), int(self.size) + 1):
      for y in range(-int(self.size), int(self.size) + 1):
        if f.inside((x, y), (0, 0), self.size):
          bl.append(BusinessLocation(self, (x, y)))
    return bl

  def business_populate(self, ratio):
    '''
    Fills the city with businesses. The ratio specifies what percentage of the
      business locations will be filled initially.
    '''
    nl = len(self.business_locations)
    fill_indices = sample(range(nl), int(nl * ratio))
    for i in fill_indices:
      bt = choice(self.btypes)
      bt.startup(self, self.business_locations[i].location,
                 f.generate_business_name())

  def pop_density_rand(self):
    '''
    Returns a location tuple for a new person in the city
    Samples randomly based on population density
    Currently: normal distribution in both X and Y directions
    '''
    loc = (self.size + 1, 0)
    while f.distance(loc, (0, 0)) > self.size:
      loc = (norm().rvs(scale = self.size, norm().rvs(scale = self.size)
    return loc

  def bizfail(self, business):
    '''
    Clean up a dead business
    '''
    self.failed_businesses.append(business)
    self.businesses.remove(business)
    self.business_locations[business.location].free()

  def city_cycle(self):
    '''
    Runs one life-cycle for the whole city
    1) People generate needs
    2) Empty business locations try to fill
    3) People fulfill needs
    4) Businesses pay billz and maybe die
    '''
    self.age += 1
    for p in self.people:
      p.generate()
    for bl in self.business_locations:
      if bl.available:
        best = 0
        best_type = None
        for bt in self.btypes:
          s = bt.startup_score(self, bl)
          if s > best:
            best = s
            best_type = bt
        if best >= 1:
          best_type.startup(self, bl, f.generate_business_name())
    for p in self.people:
      p.fulfill()
    for b in self.businesses:
      b.burn()

  def life(self, ncycles):
    '''
    The main module! Runs n cycles of life in the city.
    Add statistical or plotting functions as desired.
    '''
    for i in xrange(ncycles):
      self.city_cycle()


class Person(object):
  def __init__(self, city, name):
    self.city = city
    self.name = name
    self.location = city.pop_density_rand()
    self.needs = self.init_needs()

  def init_needs(self):
    needs = {}
    for n in self.city.dtypes:
      needs[n] = 0
    return needs

  def cycle(self):
    '''
    Runs one life-cycle for the person
    '''
    self.generate()
    self.fulfill()

  def generate(self):
    '''
    Randomly generates this cycle's demand based on needs
    '''
    for n in self.city.dtypes:
      self.needs[n] += poisson.rvs(self.city.dtypes[n].dlambda) * \
                               self.city.dtypes[n].dprice

  def fulfill(self):
    '''
    Tries to fulfill needs at nearby businesses
    '''
    pass

class Business(object):
  def __init__(self, city, name, blocation, btype):
    self.city = city
    self.name = name
    self.blocation = blocation
    self.blocation.fill()
    self.btype = btype
    self.cash = biztype.initial_cash
    self.birthday = city.age
    self.deathday = None
    self.lifespan = None

  def burn(self):
    '''
    Pay the billz for this cycle.
    '''
    self.cash -= self.btype.burnrate
    if self.cash < 0:
      self.die()

  def die(self):
    '''
    Clear location for some other business to take over
    '''
    self.deathday = self.city.age
    self.lifespan = self.deathday - self.birthday
    self.city.bizfail(self)

class BusinessLocation(object):
  def __init__(self, city, location):
    self.city = city
    self.location = location
    self.available = True

  def free(self):
    self.available = True

  def fill(self):
    self.available = False

class BusinessType(object):
  def __init__(self, bname, init_cash, init_need_threshold,
               init_need_radius, burnrate):
    self.bname = btype
    self.initial_cash = init_cash
    self.initial_need_threshold = init_need_threshold
    self.initial_need_radius = init_need_radius
    self.burnrate = burnrate

  def startup_score(self, city, blocation):
    '''
    Determines how good this location would be to start a business of this type
    Must be >= 1 to trigger a startup
    '''
    pass

  def startup(self, city, blocation, name):
    '''
    Starts a business of this type in that location!
    '''
    self.city.businesses.append(Business(city, name, blocation, self))

class DemandType(object):
  def __init__(self, dname, dlambda, dprice):
    self.dname = dname
    self.dlambda = dlambda
    self.dprice = dprice

  def demand_radius(self, need):
    '''
    Determines the radius that a person will go to fulfill this type of need
      given the quantity of need
    '''
    pass
