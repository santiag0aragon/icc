from analyzer import Analyzer
from detector import Detector
import grgsm
import os

def run_detectors(found_list):
    pass

if __name__ == '__main__':
    udp_port = 4927

    detector = Detector(udp_port)

    detector.start()

    arfcn = 0
    # fc = 933.6e6 #Spiegel cell tower
    fc = 936.2e6
    sample_rate = 2e6
    ppm = 0 #frequency offset in ppm
    gain = 30


    #Get the arfcn
    # for band in grgsm.arfcn.get_bands():
    #     if grgsm.arfcn.is_valid_downlink(fc, band):
    #         arfcn = grgsm.arfcn.downlink2arfcn(fc, band)
    #         print arfcn
    #         break

    # print("ARFCN: " + str(arfcn))

    channels_num = int(sample_rate/0.2e6)
    to_scan = ['P-GSM',
                   'E-GSM',
                   'R-GSM']
    for band in to_scan:
        print "\nScanning band: %s"% band


        first_arfcn = grgsm.arfcn.get_first_arfcn(band)
        last_arfcn = grgsm.arfcn.get_last_arfcn(band)
        last_center_arfcn = last_arfcn - int((channels_num / 2) - 1)

        current_freq = grgsm.arfcn.arfcn2downlink(first_arfcn + int(channels_num / 2) - 1, band)
        last_freq = grgsm.arfcn.arfcn2downlink(last_center_arfcn, band)
        stop_freq = last_freq + 0.2e6 * channels_num

        print 'stop freq %s ' % stop_freq
        while current_freq < stop_freq:
            print 'current freq %s ' % current_freq
            # silence rtl_sdr output:
            # open 2 fds
            null_fds = [os.open(os.devnull, os.O_RDWR) for x in xrange(2)]
            # save the current file descriptors to a tuple
            save = os.dup(1), os.dup(2)
            # put /dev/null fds on 1 and 2
            os.dup2(null_fds[0], 1)
            os.dup2(null_fds[1], 2)


            analyzer = Analyzer(fc=fc, gain=gain, samp_rate=sample_rate,
                        ppm=ppm, arfcn=arfcn, capture_id="test0",
                        udp_ports=[udp_port], rec_length=6, max_timeslot=2,
                        verbose=False, test=False)
            analyzer.start()
            analyzer.wait()
            analyzer.stop()
            scanner = None
            current_freq += channels_num * 0.2e6

    detector.stop()
