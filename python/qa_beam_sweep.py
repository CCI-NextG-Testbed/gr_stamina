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
from beam_sweep import beam_sweep
from beam_to_gpio import beam_to_gpio
import time

class qa_beam_sweep(gr_unittest.TestCase):

    def setUp(self):
        self.tb = gr.top_block()

    def tearDown(self):
        self.tb = None

    def test_001_t(self):
        # set up fg
        src = beam_sweep(
            mhu=1,
            start_beam=0,
            end_beam=3,
            sweep='exhaustive',
            period=0.1,
            debug=False
        )

        dst = blocks.message_debug()

        self.tb.msg_connect((src, 'beam_id'), (dst, 'print'))

        self.tb.start()


        time.sleep(1)

        self.tb.stop()
        self.tb.wait()

        # check data

    def test_002_t(self):
        # set up fg
        src = beam_sweep(
            mhu=1,
            start_beam=0,
            end_beam=63,
            sweep='exhaustive',
            period=0.1,
            debug=False
        )


        mid = beam_to_gpio(
            mhu1_beam_index=32,
            mhu2_beam_index=32,
            mhu1_mode='TX',
            mhu2_mode='TX',
            debug=True
            #  debug=False
        )

        dst = blocks.message_debug()

        self.tb.msg_connect((src, 'beam_id'), (mid, 'beam_id'))
        self.tb.msg_connect((mid, 'gpio_cmd'), (dst, 'print'))


        self.tb.start()


        time.sleep(3)

        self.tb.stop()
        self.tb.wait()


    def test_003_t(self):
        # set up fg
        src = beam_sweep(
            mhu=1,
            sweep='custom',
            iterable=range(1,5),
            period=[0.1, 0.2, 0.3, 0.4],
            debug=False
        )

        dst = blocks.message_debug()

        self.tb.msg_connect((src, 'beam_id'), (dst, 'print'))

        self.tb.start()


        time.sleep(5)

        self.tb.stop()
        self.tb.wait()



    def rest_004_t(self):

        # set up fg
        src = beam_sweep(
            mhu=1,
            start_beam=0,
            end_beam=63,
            sweep='exhaustive',
            period=0.1,
            debug=False
        )


        mid = beam_to_gpio(
            mhu1_beam_index=32,
            mhu2_beam_index=32,
            mhu1_mode='TX',
            mhu2_mode='TX',
            debug=True
            #  debug=False
        )

        dst = blocks.message_debug()

        self.tb.msg_connect((src, 'beam_id'), (mid, 'beam_id'))
        self.tb.msg_connect((mid, 'gpio_cmd'), (dst, 'print'))


        self.tb.start()


        time.sleep(3)

        self.tb.stop()
        self.tb.wait()




if __name__ == '__main__':
    gr_unittest.run(qa_beam_sweep)
