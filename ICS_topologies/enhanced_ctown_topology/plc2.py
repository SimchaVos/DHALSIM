from minicps.devices import PLC
from utils import PLC2_DATA, STATE, PLC2_PROTOCOL
from utils import T1, ENIP_LISTEN_PLC_ADDR, CTOWN_IPS
import csv
from datetime import datetime
import logging
from decimal import Decimal
import time
import signal
import sys

import thread
import threading

plc2_log_path = 'plc2.log'


class PLC2(PLC):

    def send_system_state(self, a, b):
        """
        This method sends the values to the SCADA server or any other client requesting the values
        :param a:
        :param b:
        :return:
        """
        while self.reader:
            self.send(T1, self.t1, ENIP_LISTEN_PLC_ADDR)

    def sigint_handler(self, sig, frame):
        self.write_output()
        sys.exit(0)

    def write_output(self):
        print 'DEBUG plc2 shutdown'
        with open('output/plc2_saved_tank_levels_received.csv', 'w') as f:
            writer = csv.writer(f)
            writer.writerows(self.saved_tank_levels)

    def pre_loop(self):
        print 'DEBUG: plc2 enters pre_loop'
        self.local_time = 0

        # Flag used to stop the thread
        self.reader = True

        self.saved_tank_levels = [["iteration", "timestamp", "T1"]]

        signal.signal(signal.SIGINT, self.sigint_handler)
        signal.signal(signal.SIGTERM, self.sigint_handler)

        self.t1 = Decimal(self.get(T1))

        self.lock = threading.Lock()
        thread.start_new_thread(self.send_system_state,(0,0))

    def main_loop(self):
        get_error_counter = 0
        get_error_counter_limit = 100
        while True:
            try:
                with self.lock:
                    self.t1 = Decimal(self.get(T1))
            except Exception:
                get_error_counter += 1
                if get_error_counter < get_error_counter_limit:
                    continue
                else:
                    print("PLC process encountered errors, aborting process")
                    exit(0)
            self.local_time += 1
            self.saved_tank_levels.append([self.local_time, datetime.now(), self.t1])
            get_error_counter = 0
            #print("Tank Level 1 %f " % self.t1)
            #print("ITERATION %d ------------- " % self.local_time)

if __name__ == "__main__":
    plc2 = PLC2(
        name='plc2',
        state=STATE,
        protocol=PLC2_PROTOCOL,
        memory=PLC2_DATA,
        disk=PLC2_DATA)