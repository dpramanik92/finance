import numpy as np
import emcee

class EmceeMCMC:
    def __init__(self, prior_func, likelihood_func, observed_data):
        """
        Initialize the Emcee MCMC simulator.

        :param prior_func: Function representing the prior distribution.
        :param likelihood_func: Function representing the likelihood of the data given the variable.
        :param observed_data: Vector of observed data (size N).
        """
        self.prior_func = prior_func
        self.likelihood_func = likelihood_func
        self.observed_data = observed_data

    def log_probability(self, params):
        """
        Compute the log of the posterior probability.

        :param params: Parameters for which to compute the posterior probability.
        :return: Log posterior probability.
        """
        prior = self.prior_func(params)
        if prior <= 0:
            return -np.inf  # Log of zero is negative infinity

        likelihood = self.likelihood_func(params, self.observed_data)
        return np.log(prior) + np.log(likelihood)

    def sample(self, initial_position, num_samples, num_walkers=10):
        """
        Generate samples using Emcee.

        :param initial_position: Initial position of the walkers (array of shape [num_walkers, ndim]).
        :param num_samples: Number of samples to generate.
        :param num_walkers: Number of walkers (default: 10).
        :return: Array of generated samples.
        """
        ndim = len(initial_position[0])
        sampler = emcee.EnsembleSampler(num_walkers, ndim, self.log_probability)

        # Run MCMC
        sampler.run_mcmc(initial_position, num_samples, progress=True)

        return sampler.get_chain(flat=True)