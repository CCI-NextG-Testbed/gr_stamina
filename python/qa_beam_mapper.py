#!/usr/bin/env python3
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

from gnuradio import gr, gr_unittest
from gnuradio import blocks
from beam_to_gpio import beam_to_gpio
import pmt
import time

class qa_beam_mapper(gr_unittest.TestCase):

    def setUp(self):
        self.tb = gr.top_block()

    def tearDown(self):
        self.tb = None

    def test_001_beam_to_gpio(self):

        dst = blocks.message_debug()

        src = beam_to_gpio(
            mhu1_beam_index=32,
            mhu2_beam_index=32,
            mhu1_mode='TX',
            mhu2_mode='TX',
            #  debug=True
            debug=False
        )

        self.tb.msg_connect((src, 'gpio_command'), (dst, 'store'))

        self.tb.start()

        src.mhu1_beam_index = 33

        time.sleep(2)

        self.tb.stop()
        self.tb.wait()

        self.assertEqual(pmt.to_python(
            dst.get_message(7)),
            {'gpio': {
                'mask': 2042, 'value': 1082, 'attr': 'OUT', 'bank': 'FP0'}
             },
            "Mismatch initial test string"
        )

if __name__ == '__main__':
    gr_unittest.run(qa_beam_mapper)
