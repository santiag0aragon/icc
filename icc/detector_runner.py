from analyzer import Analyzer
from detector import Detector
import grgsm

def run_detectors(found_list):
    pass

if __name__ == '__main__':
    udp_port = 4927

    detector = Detector(udp_port)

    detector.start()

    arfcn = 0
    fc = 933.6e6 #Spiegel cell tower
    sample_rate = 2000000.052982
    ppm = 90 #frequency offset in ppm
    gain = 30


    #Get the arfcn
    for band in grgsm.arfcn.get_bands():
        if grgsm.arfcn.is_valid_downlink(fc, band):
            arfcn = grgsm.arfcn.downlink2arfcn(fc, band)
            break

    print("ARFCN: " + str(arfcn))

    analyzer = Analyzer(fc=fc, gain=gain, samp_rate=sample_rate,
                        ppm=ppm, arfcn=arfcn, capture_id="test0",
                        udp_ports=[udp_port], rec_length=30, max_timeslot=2,
                        verbose=False, test=False)
    analyzer.start()
    analyzer.wait()
    detector.stop()
