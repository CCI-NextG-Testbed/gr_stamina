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
import numpy as np
from gnuradio import gr
import pmt
from time import time

class beam_selector(gr.basic_block):
    """
    Method that selects the best beam for IA
    """
    def __init__(self,
             pair_file="/home/joao/sel_pair.log",
             kpi_file="/home/joao/sel_kpi.log",
             threshold=0.0,
             debug=False
        ):

        # Check if the threshold is not a positiver number
        if threshold < 0.0:
            raise ValueError("Negative threshold:" + str(threshold) )

        gr.basic_block.__init__(self,
            name="Beam Selector",
            in_sig=None,
            out_sig=None)

        # Save parameters as class variables
        self._threshold = threshold

        logging.basicConfig(
            level=logging.DEBUG if debug else logging.INFO,
            format='[%(levelname)s] [%(name)s] %(message)s'
        )
        self.logging = logging.getLogger(self.name())

        self._sel_counter = 0
        self._kpi_counter = 0
        self._beam_store = {}

        # Register message port
        self.message_port_register_in(pmt.intern('trigger'))
        self.message_port_register_in(pmt.intern('kpi_in'))
        self.message_port_register_out(pmt.intern('sweep'))

        # Assign sweep CTL message handler
        self.set_msg_handler(pmt.intern('trigger'), self.trigger_msg_handler)
        self.set_msg_handler(pmt.intern('kpi_in'), self.val_msg_handler)

        # Open file and add headers
        self.results = open(pair_file, "w")
        self.results.write("#,TX,RX,KPI,elapsed\n")

        self.kpi = open(kpi_file, "w")
        self.kpi.write("#,TX,RX,KPI\n")

    def stop(self):
        """
        Called at the end of the flowgraph execution to free resources
        """
        self.results.close()
        self.kpi .close()

        return gr.basic_block.stop(self)


    def val_msg_handler(self, msg):
        # Convert message to python
        p_msg = pmt.to_python(msg)
        # Print debug information
        self.logging.debug(f'Received Value message: {p_msg}')

        # Check if we receive a new sweep state
        kpi = p_msg.get('val', -999.0)
        # Check if we receive  a beam ID for the TX
        tx_beam = p_msg.get('tx', 32)
        # Check if we receive  a beam ID for the RX
        rx_beam = p_msg.get('rx', 32)

        # Check if we need to create a new entry in the beam store
        if (tx_beam, rx_beam) not in self._beam_store:
            self._beam_store[(tx_beam, rx_beam)] = []

        if self.trigger:
            self._beam_store[(tx_beam, rx_beam)].append(kpi)

        self._kpi_counter += 1
        self.kpi.write(f"{self._kpi_counter},{tx_beam},{rx_beam},{kpi}\n")

    def trigger_msg_handler(self, msg):
        # Convert message to python
        p_msg = pmt.to_python(msg)
        # Print debug information
        self.logging.debug(f'Received trigger message: {p_msg}')

        # Check if we receive a new sweep state
        if 'trigger' not in p_msg:
            # Raise error
            raise ValueError('Missing references to a trigger: ' + str(p_msg))

        # Set the new value
        self.trigger = p_msg.get('trigger', True)

        # When triggered, reset saved information
        if self.trigger:
            self._sel_counter += 1
            self._beam_store = {}

        else:
            start = time()
            # Get the average KPI values per beam pair
            for beam_pair in self._beam_store:
                self._beam_store[beam_pair] = np.median(self._beam_store[beam_pair])

            if self._beam_store:
                # Extract the beam pair with highest KPI
                tx_beam, rx_beam = max(self._beam_store, key=self._beam_store.get)
                kpi = self._beam_store[(tx_beam, rx_beam)]

            # Measure elapsed time
            elapsed = time() - start

            if self._beam_store:
                # Report findings
                self.logging.info(f'Pair TX {tx_beam} RX {rx_beam} RSS {kpi} Time {elapsed}')

                # Use the best beam
                self.message_port_pub(
                    pmt.intern('sweep'),
                    pmt.to_pmt({"set_beam": {'tx': tx_beam, 'rx': rx_beam}})
                )

                self.results.write(f"{self._sel_counter},{tx_beam},{rx_beam},{kpi},{elapsed}\n")

            else:
                # Report findings
                self.logging.info(f'Failed IA, resetting to boresight')

                # Use the best beam
                self.message_port_pub(
                    pmt.intern('sweep'),
                    pmt.to_pmt({"set_beam": {'tx': 32, 'rx': 32}})
                )

                self.results.write(f"{self._sel_counter},0,0,0,{elapsed}\n")
