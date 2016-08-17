#    Copyright (C) 2016 Emmanuel Chery
#    Email: Emmanuel Chery <emmanuel.chery@ams.net>
#
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License along
#    with this program; if not, write to the Free Software Foundation, Inc.,
#    51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
###############################################################################

"""OpenReliability physics constants and predefined functions."""

from scipy import stats, constants
from math import exp, log

# Physics constants
c = constants.c
eps_0 = constants.epsilon_0
eV = constants.e
h = constants.h
hbar = constants.hbar
k = constants.Boltzmann
mu_0 = constants.mu_0
N_A = constants.Avogadro
Pi = constants.pi
q = constants.e
R = constants.R



# Usual functions

def inCelsius(T):
    """Return the temperature in Celsius"""
    if T >= 0:
            return(T - 273.15)
    else:
        raise Exception('Negative temperature provided')

def inKelvin(T):
    """Return the temperature in Kelvin"""
    if T >= -273.15:
            return(T + 273.15)
    else:
        raise Exception('Temperature below absolute zero provided')

def fracEstim(v):
    """Calculate the fraction estimator for a given vector v."""
    rank = stats.rankdata(v)
    return((rank-0.3)/(len(v)+0.4)*100)

def qnorm(p):
    """Return the standard deviation for a given probability"""
    return(stats.norm.ppf(p))

def pnorm(q):
    """Return the probability for a given standard deviation"""
    return(stats.norm.cdf(q))

def qweibull(p):
    """Return the weibit for a given probability"""
    try:
        return(log(-log(1-p)))
    except ValueError:
        print("Error: rank cannot be egal to 0 or 1 for a Weibull distribution.")

def pweibull(q):
    """Return the probability for a given weibit"""
    return(1-exp(-exp(q)))
