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

import logging
import numpy
import pmt
from copy import copy
from gnuradio import gr
from time import sleep
import numpy as np

from datetime import datetime
from threading import Thread, Lock, Event


class kpi_agg(gr.sync_block):
    """
    docstring for block kpi_agg
    """
    def __init__(
        self,
        beam_file="/home/joao/kpi_beam.log",
        meas_file="/home/joao/kpi_meas.log",
        standalone=False,
        meas_period=300e-6,
        sensitivity=-90.0,
        debug=False
    ):

        gr.sync_block.__init__(self,name='KPI Aggregator',
                               in_sig=[numpy.float32],
                               out_sig=None)

        # Register message ports
        self.message_port_register_in(pmt.intern('beam_id'))
        self.message_port_register_in(pmt.intern('trigger'))
        self.message_port_register_out(pmt.intern('kpi_out'))

        # Assign beam ID message handler
        self.set_msg_handler(pmt.intern('beam_id'), self.beam_id_msg_handler)
        self.set_msg_handler(pmt.intern('trigger'), self.trigger_msg_handler)

        # Set class variables
        self._meas_period = meas_period
        self._sensitivity = sensitivity
        self._trigger = standalone

        logging.basicConfig(
            level=logging.DEBUG if debug else logging.INFO,
            format='[%(levelname)s] [%(name)s] %(message)s'
        )
        self.logging = logging.getLogger(self.name())

        self.tx_beam_index = 0
        self.rx_beam_index = 0
        self.measurement = -999

        # Create a thread to run our sweep
        self._thread = Thread(target=self.measure)
        # Control flag to keep thread alive
        self._finished = Event()
        # Creave event to drop samples
        self._beam_change = Event()
        # Create lock to enforce atomic operations
        self._lock = Lock()

        # Create files to save log information
        self.beam_log = open(beam_file, "w")
        self.beam_log.write("measurement,TX,RX\n")
        self.meas_log = open(meas_file, "w")
        self.meas_log.write("measurement,TX,RX,KPI\n")

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

        # Close files we left open
        self.meas_log.close()
        self.beam_log.close()

        return gr.sync_block.stop(self)

    def work(self, input_items, output_items):
        # If triggered and set to work
        if self._trigger and self.tx_beam_index and self.rx_beam_index:
            # Get the most recent sample
            measurement = np.mean(input_items[0])

            # Check whether the measurement is above sensitivity
            if  float(measurement) > self._sensitivity:
                # With the lock
                with self._lock:
                   self.measurement = measurement

        return len(input_items[0])

    def measure(self):
        """
        Periodically collected measurements
        """
        # Empty containert to hold measurements
        measurement_dict = {}

        # While our thread is going on
        while not self._finished.is_set():
            # If not trigger, keep waiting
            if not self._trigger:
                sleep(1e-9)

            # Or else, let's go!
            else:
                # If there was a recent beam change, skip measurements
                if self._beam_change.is_set():
                    # Clear the flag and move on
                    self._beam_change.clear()

                # If there is no change, report measurements
                elif self.tx_beam_index and self.rx_beam_index:
                    # With the lock, get a copy of the values we need
                    with self._lock:
                        # Update measurement dict
                        measurement_dict = {
                            "val": float(copy(self.measurement)),
                            "tx": copy(self.tx_beam_index),
                            "rx": copy(self.rx_beam_index)
                        }

                    # Convert GPIO dict to PMT and sent control port message
                    self.message_port_pub(
                        pmt.intern('kpi_out'),
                        pmt.to_pmt(measurement_dict)
                    )

                    # We need the lock to prevent variable change before writing
                    self.meas_log.write(
                        f"{datetime.now().strftime('%H:%M:%S.%f')}," + \
                        f"{measurement_dict['tx']},{measurement_dict['rx']}," \
                        f"{measurement_dict['val']}\n"
                    )


                # Wait for the next measurement period
                sleep(self._meas_period)

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
        self._trigger = p_msg.get('trigger', True)


    def beam_id_msg_handler(self, msg):
        # Convert message to python
        p_msg = pmt.to_python(msg)
        # Print debug information
        self.logging.debug(f'Received Beam ID message: {p_msg}')

        # If triggered to work
        if self._trigger:
            # If we have no references to TX or RX
            if 'tx' not in p_msg or 'rx' not in p_msg:
                # Raise error
                raise ValueError('Missing references to any antenna: ' + str(p_msg))

            # With the lock
            with self._lock:
                # Check if we receive  a beam ID for the TX
                self.tx_beam_index = p_msg.get('tx', 32)
                # Check if we receive  a beam ID for the RX
                self.rx_beam_index = p_msg.get('rx', 32)
                # Flag we had a beam change
                self._beam_change.set()

            # We don't need the lock to write the metrics onto a file
            self.beam_log.write(
                f"{datetime.now().strftime('%H:%M:%S.%f')}," + \
                f"{self.tx_beam_index},{self.rx_beam_index}\n"
            )
