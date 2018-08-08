#!/usr/bin/env python
"""
Simpler version of Joe Zuntz naval analogy
"""
from __future__ import print_function

from mpi4py import MPI
from .comm import Comm

ADMIRAL    = 0

GO_ASHORE  = 0
WORK = 1

comm = Comm()
rank = comm.rank
nships = comm.size-1

class Admiral(object):
    """
    The admiral send orders to the fleet, and gathers
    reports

    The admiral does not other work
    """
    def __init__(self, orders, save_reports=True):
        self.orders=orders[:]
        self.status = MPI.Status()

        self.fleet=get_fleet()
        self.ships_at_sea=[]

        self.save_reports=save_reports
        self._reports=[]

    def orders_remain(self):
        """
        True if there are any orders remaining
        """
        return len(self.orders) > 0

    def send_order(self, ship):
        """
        send the next order to the specified ship
        """
        order = self.orders.pop()
        comm.send(order, dest=ship, tag=WORK)

    def send_ashore(self, ship):
        """
        send a ship ashore
        """
        print("sending",ship,"ashore")
        comm.send(-1, dest=ship, tag=GO_ASHORE)
        self.ships_at_sea.remove(ship)

    def await_report(self):
        """
        await a report from a ship
        """
        report = comm.recv(
            source=MPI.ANY_SOURCE,
            tag=MPI.ANY_TAG,
            status=self.status,
        )
        ship = self.status.source

        return report, ship

    def deploy_fleet(self):
        """
        deploy the entire fleet and reset the reports
        """

        self.ships_at_sea = self.fleet[:]
        self._reports=[]

    def recall_fleet(self):
        """
        bring home all remaining ships
        """
        ships_to_recall=self.ships_at_sea[:]
        for ship in ships_to_recall:
            self.send_ashore(ship)

    def orchestrate(self):
        """
        deploy the fleet and send out the orders

        parameters
        ----------
        save_reports: bool, optional
            If True, save the reports in the .reports attribute
        """


        self.deploy_fleet()

        for ship in self.fleet:
            if self.orders_remain():
                self.send_order(ship)
            else:
                self.send_ashore(ship)
        
        while self.orders_remain():

            # wait for a report
            report, ship = self.await_report()

            if self.save_reports:
                self._reports.append(report)

            # send the reporting ship a new order
            self.send_order(ship)        
        
        # No more work to be done, wait for one report
        # from each ship at sea

        for tship in self.ships_at_sea:
            report, ship = self.await_report()

            if self.save_reports:
                self._reports.append(report)

        self.recall_fleet()

    @property
    def reports(self):
        if hasattr(self,'_reports'):
            return self._reports
        else:
            raise RuntimeError("reports were not saved")

class Ship(object):
    """
    The ship receives orders, carries them out, and sends back
    a report
    """
    def __init__(self, function):
        self.function=function
        self.rank=rank
        self.status = MPI.Status()

    def go(self):
        """
        carry out tasks using the specified function
        """

        while True:
            # Receive a message from the master
            order, should_go_ashore = self.await_order()

            if should_go_ashore:
                print("ship",self.rank,"heading ashore")
                break

            report = self.carry_out_order(order)
            self.send_report(report)

    def send_report(self, report):
        """
        send the report to the admiral
        """
        comm.send(report, dest=ADMIRAL, tag=0)

    def carry_out_order(self,order):
        """
        perform the task
        """
        report = self.function(order)
        return report

    def await_order(self):
        """
        wait for an order from the admiral
        """
        order = comm.recv(
            source=ADMIRAL,
            tag=MPI.ANY_TAG,
            status=self.status,
        )
        if self.status.tag == GO_ASHORE:
            should_go_ashore=True
        else:
            should_go_ashore=False

        return order, should_go_ashore

def get_fleet():
    """
    get a list of all ships in the fleet
    """
    return list(range(1,nships+1))

def example():
    import numpy

    def relocate(seed):
        """
        relocate to a random lon,lat
        """
        numpy.random.seed(seed)
        lonlat = numpy.random.uniform(size=2)
        return lonlat

    if rank==ADMIRAL:
        njobs = 13
        numpy.random.seed(31415)
        seeds = list(numpy.random.randint(0,high=2**30,size=njobs))

        admiral = Admiral(seeds)
        admiral.orchestrate()
    else:
        ship = Ship(relocate)
        ship.go()

if __name__=="__main__":
    example()
