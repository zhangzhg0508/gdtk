-- Auto-generated by prep-gas on: 20-Jun-2022 10:54:34

model = 'CompositeGas'
species = {'N2', }

physical_model = 'thermally-perfect-gas'
energyModes = {'equilibrium'}
db = {}
db['N2'] = {}
db['N2'].atomicConstituents = { N=2, }
db['N2'].charge = 0
db['N2'].M = 2.80134000e-02
db['N2'].sigma = 3.62100000
db['N2'].epsilon = 97.53000000
db['N2'].Lewis = 1.15200000
db['N2'].thermoCoeffs = {
  origin = 'CEA',
  nsegments = 3, 
  T_break_points = { 200.00, 1000.00, 6000.00, 20000.00, },
  T_blend_ranges = { 400.0, 1000.0, },
  segment0 = {
    2.210371497e+04,
   -3.818461820e+02,
    6.082738360e+00,
   -8.530914410e-03,
    1.384646189e-05,
   -9.625793620e-09,
    2.519705809e-12,
    7.108460860e+02,
   -1.076003744e+01,
  },
  segment1 = {
    5.877124060e+05,
   -2.239249073e+03,
    6.066949220e+00,
   -6.139685500e-04,
    1.491806679e-07,
   -1.923105485e-11,
    1.061954386e-15,
    1.283210415e+04,
   -1.586640027e+01,
  },
  segment2 = {
    8.310139160e+08,
   -6.420733540e+05,
    2.020264635e+02,
   -3.065092046e-02,
    2.486903333e-06,
   -9.705954110e-11,
    1.437538881e-15,
    4.938707040e+06,
   -1.672099740e+03,
  },
}
db['N2'].viscosity = {
   model = 'CEA',
   nsegments = 3,
   segment0 = {
      T_lower = 200.0,
      T_upper = 1000.0,
      A =  6.2526577e-01,
      B = -3.1779652e+01,
      C = -1.6407983e+03,
      D =  1.7454992e+00,
   },
   segment1 = {
      T_lower = 1000.0,
      T_upper = 5000.0,
      A =  8.7395209e-01,
      B =  5.6152222e+02,
      C = -1.7394809e+05,
      D = -3.9335958e-01,
   },
   segment2 = {
      T_lower = 5000.0,
      T_upper = 15000.0,
      A =  8.8503551e-01,
      B =  9.0902171e+02,
      C = -7.3129061e+05,
      D = -5.3503838e-01,
   },
}
db['N2'].thermal_conductivity = {
   model = 'CEA',
   nsegments = 3,
   segment0 = {
      T_lower = 200.0,
      T_upper = 1000.0,
      A =  8.5439436e-01,
      B =  1.0573224e+02,
      C = -1.2347848e+04,
      D =  4.7793128e-01,
   },
   segment1 = {
      T_lower = 1000.0,
      T_upper = 5000.0,
      A =  8.8407146e-01,
      B =  1.3357293e+02,
      C = -1.1429640e+04,
      D =  2.4417019e-01,
   },
   segment2 = {
      T_lower = 5000.0,
      T_upper = 15000.0,
      A =  2.4176185e+00,
      B =  8.0477749e+03,
      C =  3.1055802e+06,
      D = -1.4517761e+01,
   },
}
