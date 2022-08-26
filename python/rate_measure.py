#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2022 Virginia Tech.
#
# This is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3, or (at your option)
# any later version.
#
# This software is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this software; see the file COPYING.  If not, write to
# the Free Software Foundation, Inc., 51 Franklin Street,
# Boston, MA 02110-1301, USA.
#

import pmt
import logging
import numpy as np
from gnuradio import gr
from time import sleep
from threading import Thread, Lock, Event
from datetime import datetime

class rate_measure(gr.sync_block):
    """
    docstring for block rate_measure
    """
    def __init__(self, meas_file="/home/joao/rate_meas.log", meas_period=1e-3,
                 debug=False):

        gr.sync_block.__init__(self,
            name="Rate Measure",
            in_sig=[np.int8],
            out_sig=None)

        self.message_port_register_in(pmt.intern('trigger'))
        self.set_msg_handler(pmt.intern('trigger'), self.trigger_msg_handler)
        self.trigger = False

        logging.basicConfig(
            level=logging.DEBUG if debug else logging.INFO,
            format='[%(levelname)s] [%(name)s] %(message)s'
        )
        self.logging = logging.getLogger(self.name())

        self._meas_period = meas_period
        self._num_samples = 0

        # Create a thread to run our sweep
        self._thread = Thread(target=self.measure)
        # Control flag to keep thread alive
        self._finished = Event()
        self._lock = Lock()

        # Create files to save log information
        self.meas_log = open(meas_file, "w")
        self.meas_log.write("measurement,throughput,overhead\n")

    def start(self):
        """
        Called at the beginning of the flowgraph execution to allocate resources
        """
        # Start our thread
        self._thread.start()

        return gr.sync_block.start(self)

    def stop(self):
        """
        Called at the end of the flowgraph execution to free resources
        """
        # Toggle flag to stop thread and join it
        self._finished.set()
        self._thread.join()

        return gr.sync_block.stop(self)

    def trigger_msg_handler(self, msg):
        # Convert message to python
        p_msg = pmt.to_python(msg)
        # Print debug information
        self.logging.debug(f'Received trigger message: {p_msg}')

        # Check if we receive a new sweep state
        if 'trigger'  not in p_msg:
            # Raise error
            raise ValueError('Missing trigger references: ' + str(p_msg))

        # Set the new value
        self.trigger = p_msg.get('trigger', True)

    def measure(self):
        """
        Periodically collected measurements
        """
        # While our thread is going on
        while not self._finished.is_set():
            # Wait for the next measurement period
            sleep(self._meas_period)

            # Start with rate zero
            thx_rate = 0
            ovd_rate = 0

            # With the lock
            with self._lock:
                # If the IA is happening, it is all overhead
                if self.trigger:
                    # Update the rate according to the measured samples and zero it
                    ovd_rate = self._num_samples / self._meas_period
                    thx_rate = 0

                # Otherwise, it is all throughout
                else:
                    # Update the rate according to the measured samples and zero it
                    ovd_rate = 0
                    thx_rate = self._num_samples / self._meas_period

                # Reset sample count
                self._num_samples = 0

            # Dump the rate onto a file
            self.meas_log.write(
                f"{datetime.now().strftime('%H:%M:%S.%f')},{thx_rate},{ovd_rate}\n"
            )

        # Close files we left open
        self.meas_log.close()

    def work(self, input_items, output_items):
        # With the lock, update the number of samples so far
        with self._lock:
            self._num_samples += len(input_items[0])

        return len(input_items[0])
