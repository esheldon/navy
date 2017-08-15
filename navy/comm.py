import time
from mpi4py import MPI

class Comm(MPI.Intracomm):
    """
    Wrapper to mpi4py's MPI.Intracomm class to avoid busy-waiting in
    recv.

    just the recv method pulled from the Comm class here

    https://raw.githubusercontent.com/lsst/ctrl_pool/master/python/lsst/ctrl/pool/pool.py
    """

    def __new__(cls,
                comm=MPI.COMM_WORLD,
                sleep=0.1):
        """
        parameters
        ----------
        comm:  MPI.Intracomm to wrap a duplicate of
            Default MPI.COMM_WORLD
        sleep: float
            Sleep time (seconds) for recv()
        """
        self = super(Comm, cls).__new__(cls, comm.Dup())
        self._sleep = sleep
        return self

    def recv(self, obj=None, source=0, tag=0, status=None):
        """
        Version of comm.recv() that doesn't busy-wait
        """
        sts = MPI.Status()
        while not self.Iprobe(source=source, tag=tag, status=sts):
            time.sleep(self._sleep)

        return super(Comm, self).recv(
            buf=obj,
            source=sts.source,
            tag=sts.tag,
            status=status,
        )



