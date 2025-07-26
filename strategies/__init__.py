"""
Strategy Analysis Package

This package provides tools for financial strategy analysis,
including MCMC sampling and statistical utilities.

Classes:
    EmceeMCMC: A class for Markov Chain Monte Carlo sampling using emcee
Functions:
    gaussian_prior: Creates a Gaussian prior distribution for MCMC sampling
"""

from .utils import EmceeMCMC, gaussian_prior

__version__ = "0.1.0"
__author__ = "Dipyaman"

__all__ = ['EmceeMCMC', 'gaussian_prior']