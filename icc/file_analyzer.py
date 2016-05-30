from gnuradio import blocks
from gnuradio import eng_notation
from gnuradio import gr
from gnuradio.eng_option import eng_option
from gnuradio.filter import firdes
from math import pi
from optparse import OptionParser

import grgsm
import osmosdr
import pmt
import signal
import sys
import click

"""
Block that reads a capture file.
"""

class FileAnalyzer(gr.top_block):

    def __init__(self, filename, samp_rate, arfcn, chan_mode='BCCH', udp_port=4000, timeslot=0, verbose=True, args="", connectToSelf=False):
        """
        """

        gr.top_block.__init__(self, "FileAnalyzer")

        ##################################################
        # Parameters
        ##################################################

        self.arfcn = arfcn
        for band in grgsm.arfcn.get_bands():
            if grgsm.arfcn.is_valid_arfcn(self.arfcn, band):
                self.fc = grgsm.arfcn.arfcn2downlink(arfcn, band)
                break

        self.samp_rate = samp_rate
        self.arfcn = arfcn
        self.udp_port = udp_port
        self.verbose = verbose
        self.cfile = filename.encode('utf-8')
        self.timeslot = timeslot
        self.chan_mode = chan_mode

        ##################################################
        # Processing Blocks
        ##################################################

        self.file_source = blocks.file_source(gr.sizeof_gr_complex*1, self.cfile, False)
        self.receiver = grgsm.receiver(4, ([0]), ([]))
        if self.fc is not None:
            self.input_adapter = grgsm.gsm_input(ppm=0, osr=4, fc=self.fc, samp_rate_in=self.samp_rate)
            self.offset_control = grgsm.clock_offset_control(self.fc)
        else:
            self.input_adapter = grgsm.gsm_input(ppm=0, osr=4, samp_rate_in=self.samp_rate)

        self.bursts_printer = grgsm.bursts_printer(pmt.intern(""), True, True, True, True)

        self.timeslot_filters = []
        for i in range(0, self.timeslot + 1):
            self.timeslot_filters.append(grgsm.burst_timeslot_filter(i))

        self.dummy_burst_filters = []
        for i in range(0, self.timeslot + 1):
            self.dummy_burst_filters.append(grgsm.dummy_burst_filter())

        #self.timeslot_filter = grgsm.burst_timeslot_filter(self.timeslot)
        #self.dummy_burst_filter = grgsm.dummy_burst_filter()

        self.other_demappers = []
        #Control channel demapper for timeslot 0
        self.control_demapper = grgsm.universal_ctrl_chans_demapper(0, ([2,6,12,16,22,26,32,36,42,46]), ([1,2,2,2,2,2,2,2,2,2]))

        #Demapping other timeslots than 0 to BCCH does not really make sense
        # if self.chan_mode == 'BCCH':
        #     #Control channel demapper for other timeslots
        #     for i in range(1, self.timeslot + 1):
        #         self.other_demappers.append(grgsm.universal_ctrl_chans_demapper(0, ([2,6,12,16,22,26,32,36,42,46]), ([1,2,2,2,2,2,2,2,2,2])))
        #     #self.bcch_demapper = grgsm.universal_ctrl_chans_demapper(0, ([2,6,12,16,22,26,32,36,42,46]), ([1,2,2,2,2,2,2,2,2,2]))
        #     #This is for a newer version of grgsm
        #     #self.bcch_demapper = grgsm.gsm_bcch_ccch_demapper(self.timeslot)
        if self.chan_mode == 'BCCH_SDCCH4':
            for i in range(1, self.timeslot + 1):
                self.other_demappers.append(grgsm.universal_ctrl_chans_demapper(self.timeslot,
                                                                            ([2, 6, 12, 16, 22, 26, 32, 36, 42, 46]),
                                                                            ([1, 2, 2, 2, 7, 7, 7, 7, 135, 135])))
            #self.bcch_sdcch4_demapper = grgsm.gsm_bcch_ccch_sdcch4_demapper(self.timeslot)
        elif self.chan_mode == 'SDCCH8':
            for i in range(1, self.timeslot + 1):
                self.other_demappers.append(grgsm.universal_ctrl_chans_demapper(i, ([0, 4, 8, 12, 16, 20, 24, 28, 32, 36, 40, 44]), ([8, 8, 8, 8, 8, 8, 8, 8, 136, 136, 136, 136])))
            #self.sdcch8_demapper = grgsm.universal_ctrl_chans_demapper(self.timeslot, ([0, 4, 8, 12, 16, 20, 24, 28, 32, 36, 40, 44]), ([8, 8, 8, 8, 8, 8, 8, 8, 136, 136, 136, 136]))
            #This is for a newer version of grgsm
            #self.sdcch8_demapper = grgsm.gsm_sdcch8_demapper(self.timeslot)
        else:
            for i in range(1, self.timeslot + 1):
                self.other_demappers.append(grgsm.universal_ctrl_chans_demapper(i, ([0, 4, 8, 12, 16, 20, 24, 28, 32, 36, 40, 44]), ([8, 8, 8, 8, 8, 8, 8, 8, 136, 136, 136, 136])))

        #TODO add demappers for all timeslots
        #self.sdcch8_demapper = grgsm.universal_ctrl_chans_demapper(self.timeslot, ([0, 4, 8, 12, 16, 20, 24, 28, 32, 36, 40, 44]), ([8, 8, 8, 8, 8, 8, 8, 8, 136, 136, 136, 136]))

        self.decoders = []
        for i in range(0, self.timeslot + 1):
            self.decoders.append(grgsm.control_channels_decoder())
        #self.cch_decoder = grgsm.control_channels_decoder()

        #Server socket
        if connectToSelf:
            self.serversocket = blocks.socket_pdu("UDP_SERVER", "127.0.0.1", str(self.udp_port), 10000)

        self.socket_pdu = blocks.socket_pdu("UDP_CLIENT", "127.0.0.1", str(self.udp_port), 10000)
        if self.verbose:
            self.message_printer = grgsm.message_printer(pmt.intern(""), True, True, False)



        ##################################################
        # Asynch Message Connections
        ##################################################

        self.connect((self.file_source, 0), (self.input_adapter, 0))
        self.connect((self.input_adapter, 0), (self.receiver, 0))
        if self.fc is not None:
            self.msg_connect(self.offset_control, "ppm", self.input_adapter, "ppm_in")
            self.msg_connect(self.receiver, "measurements", self.offset_control, "measurements")

        #for df in self.dummy_burst_filters:
        #    self.msg_connect(self.receiver, "C0", df, "in")
        #self.msg_connect(self.receiver, "C0", self.dummy_burst_filter, "in")

        #for index, tf in enumerate(self.dummy_burst_filters):
        #    self.msg_connect(self.dummy_burst_filters[index], "out", self.timeslot_filters[index], "in")
        #self.msg_connect(self.dummy_burst_filter, "out", self.timeslot_filter, "in")

        #if self.print_bursts:
        #for tf in self.timeslot_filters:
        #    self.msg_connect(tf, "out", self.bursts_printer, 'bursts')
        #self.msg_connect(self.timeslot_filter, "out", self.bursts_printer, 'bursts')

        #Connect the timeslot 0 demapper and decoder
        #self.msg_connect(self.timeslot_filters[0], "out", self.control_demapper, "bursts")
        self.msg_connect(self.receiver, "C0", self.control_demapper, "bursts")
        self.msg_connect(self.control_demapper, "bursts", self.decoders[0], "bursts")
        self.msg_connect(self.decoders[0], "msgs", self.socket_pdu, "pdus")
        if self.verbose:
            self.msg_connect(self.decoders[0], "msgs", self.message_printer, "msgs")


        #Connect the demappers and decoders for the other timeslots
        for i in range(1, self.timeslot + 1):
            self.msg_connect(self.receiver, "C0", self.other_demappers[i-1], "bursts")
            #self.msg_connect(self.timeslot_filters[i], "out", self.other_demappers[i - 1], "bursts")
            self.msg_connect(self.other_demappers[i - 1], "bursts", self.decoders[i], "bursts")
            self.msg_connect(self.decoders[i], "msgs", self.socket_pdu, "pdus")
            if self.verbose:
                self.msg_connect(self.decoders[i], "msgs", self.message_printer, "msgs")


        # if self.chan_mode == 'BCCH':
        #     self.msg_connect(self.timeslot_filter, "out", self.bcch_demapper, "bursts")
        #
        #     self.msg_connect(self.bcch_demapper, "bursts", self.cch_decoder, "bursts")
        #     self.msg_connect(self.cch_decoder, "msgs", self.socket_pdu, "pdus")
        #     if self.verbose:
        #         self.msg_connect(self.cch_decoder, "msgs", self.message_printer, "msgs")
        #
        # elif self.chan_mode == 'BCCH_SDCCH4':
        #     self.msg_connect(self.timeslot_filter, "out", self.bcch_sdcch4_demapper, "bursts")
        #     self.msg_connect(self.bcch_sdcch4_demapper, "bursts", self.cch_decoder, "bursts")
        #     self.msg_connect(self.cch_decoder, "msgs", self.socket_pdu, "pdus")
        #     if self.verbose:
        #         self.msg_connect(self.cch_decoder, "msgs", self.message_printer, "msgs")
        #
        # elif self.chan_mode == 'SDCCH8':
        #     self.msg_connect(self.timeslot_filter, "out", self.sdcch8_demapper, "bursts")
        #     self.msg_connect(self.sdcch8_demapper, "bursts", self.cch_decoder, "bursts")
        #     self.msg_connect(self.cch_decoder, "msgs", self.socket_pdu, "pdus")
        #     if self.verbose:
        #         self.msg_connect(self.cch_decoder, "msgs", self.message_printer, "msgs")

@click.group()
def cli():
    pass

@click.command()
@click.argument('filename')
@click.option('--sample_rate', default=2e6)
@click.option('--arfcn', default=1017)
@click.option('--timeslot', default=0)
def run(filename, sample_rate, arfcn, timeslot):
    fa = FileAnalyzer(filename, sample_rate, arfcn, timeslot=timeslot, verbose=True, connectToSelf=True)
    fa.start()
    fa.wait()
    fa.stop()


if __name__ == '__main__':
    cli.add_command(run)
    cli()
