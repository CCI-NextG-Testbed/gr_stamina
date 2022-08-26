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
import numpy as np
from time import sleep

class beam_mapper(gr.basic_block):
    """
    docstring for block beam_mapper
    """
    def __init__(self, tx_mhu="MHU1", rx_mhu="MHU2", backoff=1e-6, pulse=1e-6,
                 config_path="/home/user/gpio_map.json", debug=False):

        # List of valid names
        valid_names = ["mhu1", "MHU1", "mhu2", "MHU2", "Disabled", "Off"]

        # Check whether TX and RX and valid and not the same
        if tx_mhu not in valid_names or rx_mhu not in valid_names \
                or (tx_mhu == rx_mhu and tx_mhu not in ["Disabled", "Off"]):
            raise ValueError('Invalid TX ' + str(tx_mhu) + " RX " + str(rx_mhu))

       # Let's try to open the GPIO configuration file
        try:
            with open(config_path, 'r') as config_file:
                gpio_config = load(config_file)

        # If no go, raise error
        except IOError:
            raise FileNotFoundError(
                'Could not find model file: ' + str(config_path)
            )

        try:
            # Get ID config
            self._id_push = gpio_config["id_range"]["lower"]
            self._id_mask = 2 ** (gpio_config["id_range"]["upper"] - \
                    gpio_config["id_range"]["lower"] + 1) - 1
            # Get mode config
            self._mode_push = gpio_config["mode_range"]["lower"]
            self._mode_mask = 2 ** (gpio_config["mode_range"]["upper"] - \
                    gpio_config["mode_range"]["lower"] + 1) - 1
            # Get beam config
            self._beam_push = gpio_config["beam_range"]["lower"]
            self._beam_mask = 2 ** (gpio_config["beam_range"]["upper"] - \
                    gpio_config["beam_range"]["lower"] + 1) - 1
            # Get MHU ID config
            self._mhu_id_1 = gpio_config["radio_id"]["1"]
            self._mhu_id_2 = gpio_config["radio_id"]["2"]
            # Get MHU mode config
            self._mhu_mode_1 = gpio_config["radio_mode"]["1"]
            self._mhu_mode_2 = gpio_config["radio_mode"]["2"]

        except KeyError:
            raise KeyError( 'GPIO config file missing necessary information')

        gr.basic_block.__init__(self,
            name="Beam Mapper",
            in_sig=None,
            out_sig=None
        )

        # Register message ports
        self.message_port_register_in(pmt.intern('beam_id'))
        self.message_port_register_out(pmt.intern('gpio_cmd'))

        # Assign beam ID message handler
        self.set_msg_handler(pmt.intern('beam_id'), self.beam_id_msg_handler)

        # Set class variables
        self._backoff = backoff
        self._pulse = pulse

        logging.basicConfig(
            level=logging.DEBUG if debug else logging.INFO,
            format='[%(levelname)s] [%(name)s] %(message)s'
        )
        self.logging = logging.getLogger(self.name())

        # Start with the transmission mode bit disabled
        self._mhu1 = {"id": 1, "mode": "0X", "bit": 0, "beam_index": None}
        self._mhu2 = {"id": 2, "mode": "0X", "bit": 0, "beam_index": None}

        # Modify the MHU configuration as needed
        if tx_mhu in ["MHU1", "mhu1"]:
           self._mhu1['mode'] = "TX"
           self._mhu1['bit'] = 1

        elif tx_mhu in ["MHU2", "mhu2"]:
           self._mhu2['mode'] = "TX"
           self._mhu2['bit'] = 1

        if rx_mhu in ["MHU1", "mhu1"]:
           self._mhu1['mode'] = "RX"
        elif rx_mhu in ["MHU2", "mhu2"]:
           self._mhu2['mode'] = "RX"

    def pmt_publish(self, bank, attr, value, mask):
        """
        Factory function to facilitate the creation of PMT messages
        """
        # Create GPIO control dictionary
        gpio = {
            'gpio': {
                'bank':  bank,
                'attr':  attr,
                'value': value,
                'mask':  mask
            }
        }

        # Convert GPIO dict to PMT and sent control port message
        self.message_port_pub(
            pmt.intern('gpio_cmd'),
            pmt.to_pmt(gpio)
        )
        # And sleep a little bit
        sleep(self._backoff + self._pulse)

    def _setup(self):
        # Default masks, in case they're handy
        ONES = 0xFFF
        ZEROES = 0x000

        # Bit push to specify transmission mode
        DI_GPIO_MASK = self._mode_mask << self._mode_push
        # Bit push to specify the index
        ID_GPIO_MASK = self._id_mask << self._id_push
        # Clear the beam alignment
        BA_GPIO_MASK = self._beam_mask << self._beam_push

        # Crete GPIO pin mask
        GPIO_MASK = DI_GPIO_MASK | ID_GPIO_MASK | BA_GPIO_MASK

        # Create and send DDR dictionary to the control port
        self.pmt_publish('FP0', 'CTRL', ZEROES, GPIO_MASK)
        self.pmt_publish('FP0', 'DDR',  ONES,   GPIO_MASK)
        self.pmt_publish('FP0', 'OUT',  ZEROES, GPIO_MASK)

        # Select the transmission direction and stay with it
        ID_TX_MODE = self._mhu1['bit'] << self._mhu_mode_1 |  \
            self._mhu2['bit'] << self._mhu_mode_2

        # Burn the transmission direction during setup
        self.pmt_publish('FP0', 'OUT', ID_TX_MODE, DI_GPIO_MASK)

        self.logging.info(f"GPIO MASK {bin(GPIO_MASK)}")

    def start(self):
        """
        Called at the beginning of the flowgraph execution to allocate resources
        """

        # Setup the two MHUs
        self._setup()

        return gr.sync_block.start(self)

    @property
    def tx_beam_index(self):
        # If the MHU1 or the MHU2 was set as TX
        if self._mhu1['mode'] == 'TX':
            return self._mhu1['beam_index']

        if self._mhu2['mode'] == 'TX':
            return self._mhu2['beam_index']

    @property
    def rx_beam_index(self):
        # If the MHU1 or the MHU2 was set as RX
        if self._mhu1['mode'] == 'RX':
            return self._mhu1['beam_index']

        if self._mhu2['mode'] == 'RX':
            return self._mhu2['beam_index']

    @tx_beam_index.setter
    def tx_beam_index(self, value):
        # Sanitize input
        if not isinstance(value, int) or value not in range(1,64):
            raise ValueError('Invalid beam value: ' + str(value))

        # If the MHU1 or the MHU2 was set as TX
        if self._mhu1['mode'] == "TX":
            # Update class's private variable
            self._mhu1['beam_index'] = value
            # Generate GPIO configuration
            self.configure_gpio(mhu=self._mhu1)

        if self._mhu2['mode'] == "TX":
            # Update class's private variable
            self._mhu2['beam_index'] = value
            # Generate GPIO configuration
            self.configure_gpio(mhu=self._mhu2)


    @rx_beam_index.setter
    def rx_beam_index(self, value):
        # Sanitize input
        if not isinstance(value, int) or value not in range(1,64):
            raise ValueError('Invalid beam value: ' + str(value))

        # If the MHU1 or the MHU2 was set as TX
        if self._mhu1['mode'] == "RX":
            # Skip reconfiguration if we can
            if value != self._mhu1['beam_index']:
                # Update class's private variable
                self._mhu1['beam_index'] = value
                # Generate GPIO configuration
                self.configure_gpio(mhu=self._mhu1)

        if self._mhu2['mode'] == "RX":
            # Skip reconfiguration if we can
            if value != self._mhu2['beam_index']:
                # Update class's private variable
                self._mhu2['beam_index'] = value
                # Generate GPIO configuration
                self.configure_gpio(mhu=self._mhu2)

    def configure_gpio(self, mhu):
        # Sanitize input
        if not mhu:
            raise ValueError("Unrecognizable MHU: " + str(mhu))

        # Create the BA mask
        BA_GPIO_MASK = self._beam_mask << self._beam_push
        # Bit push with the BA value
        BA_TOGGLE = int(mhu['beam_index']) << self._beam_push
        # Convert GPIO dict to PMT and sent control port message
        self.pmt_publish('FP0', 'OUT', BA_TOGGLE, BA_GPIO_MASK)

        # Create new ID mask
        ID_GPIO_MASK = self._id_mask << self._id_push
        # Bit push to specify the MHU index
        ID_TOGGLE =  1 << (self._mhu_id_1 if mhu['id'] == 1 else self._mhu_id_2)

        # Convert GPIO dict to PMT and sent control port message
        self.pmt_publish('FP0', 'OUT', ID_TOGGLE, ID_GPIO_MASK)
        self.pmt_publish('FP0', 'OUT', 0x000, ID_GPIO_MASK)

        # Print debug information
        self.logging.debug(
            f'MHU {mhu["id"]} Beam Index {mhu["beam_index"]} ' + \
            f'BA GPIO Mask {bin(ID_GPIO_MASK)} BA Toggle {bin(ID_TOGGLE)}' + \
            f'ID GPIO Mask {bin(BA_GPIO_MASK)} ID Toggle {bin(BA_TOGGLE)}'
        )

    def beam_id_msg_handler(self, msg):
        # Convert message to python
        p_msg = pmt.to_python(msg)

        # Print debug information
        self.logging.debug(f'Received Beam ID message: {p_msg}')

        # Check if we receive  a beam ID for the TX
        if 'tx' in p_msg:
            self.tx_beam_index = p_msg.get('tx', 32)

        # Check if we receive  a beam ID for the RX
        if 'rx' in p_msg:
            self.rx_beam_index = p_msg.get('rx', 32)

        # If we have no references to TX or RX
        if 'tx' not in p_msg and 'rx' not in p_msg:
            # Raise error
            raise ValueError('Missing references to any antenna: ' + str(p_msg))
