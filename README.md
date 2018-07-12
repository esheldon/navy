# navy
simple mpi4py task queue modeled after the royal navy

based on Joe Zuntz similar code called "royal_navy.py" at https://bitbucket.org/joezuntz/im3shape-git

An example
```python
import numpy as np
import navy

def example():

    def relocate(seed):
        """
        this will be the function that does the work

        relocate the ship to a random lon,lat
        """
        np.random.seed(seed)
        lon = np.random.uniform(low=-180, max=180)
        lat = np.random.uniform(low=-90, max=90)
        return np.array([lon,lat])

    if rank==navy.ADMIRAL:
        njobs = 13
        np.random.seed(31415)
        seeds = list(np.random.randint(0,high=2**30,size=njobs))

        admiral = navy.Admiral(seeds)
        admiral.orchestrate()
    else:
        ship = navy.Ship(relocate)
		ship.go()
```
