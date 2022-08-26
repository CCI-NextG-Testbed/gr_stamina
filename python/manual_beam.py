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
from gnuradio import gr
import pmt

class manual_beam(gr.sync_block):
    """
    docstring for block manual_beam
    """
    def __init__(self,
                 tx_beam=32,
                 rx_beam=32,
                 debug=False):
        gr.sync_block.__init__(self,
            name="Manual Beam",
            in_sig=None,
            out_sig=None)

        self._tx_beam = tx_beam
        self._rx_beam = rx_beam

        logging.basicConfig(
            level=logging.DEBUG if debug else logging.INFO,
            format='[%(levelname)s] [%(name)s] %(message)s'
        )
        self.logging = logging.getLogger(self.name())

        # Register message port
        self.message_port_register_out(pmt.intern('beam_id'))

    def pmt_publish(self, tx_index=0, rx_index=0):
        """
        Factory function to facilitate the creation of PMT messages
        """
        # Start with an empty dict and add parameters according to kwargs
        beam_dict = {}
        if tx_index:
            beam_dict["tx"] = tx_index

        if rx_index:
            beam_dict["rx"] = rx_index

        # Convert GPIO dict to PMT and sent control port message
        self.message_port_pub( pmt.intern('beam_id'), pmt.to_pmt(beam_dict) )

    def start(self):
        """
        Called at the beginning of the flowgraph execution to allocate resources
        """

        # Start our block
        self.logging.debug("Setting initial beams")
        self.pmt_publish(tx_index=self._tx_beam, rx_index=self._rx_beam)

        return gr.sync_block.start(self)

    def set_tx_beam(self, tx_beam):
        if not tx_beam in range(1, 64):
            print("Invalid TX beam value:", tx_beam)

        self.logging.debug(f'Setting TX beam index to {tx_beam}')
        self._tx_beam = tx_beam

        # Start our block
        self.pmt_publish(tx_index=self._tx_beam)

    def set_rx_beam(self, rx_beam):
        if not rx_beam in range(1, 64):
            print("Invalid RX beam value:", rx_beam)

        self.logging.debug(f'Setting RX beam index to {rx_beam}')
        self._rx_beam = rx_beam

        # Start our block
        self.pmt_publish(rx_index=self._rx_beam)
