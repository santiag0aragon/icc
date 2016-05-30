from icc.runner import Runner, createDatabase
from icc.runner import listScans as lc
from icc.aux.lat_log_utils import parse_dms
import grgsm
import click
from icc.file_analyzer import FileAnalyzer
from icc.runner import offlineDetection

@click.group()
@click.option('--ppm', '-p', default=0, help='frequency offset in parts per million, default 0')
@click.option('--samplerate', '-sr', default=2e6, type=float, help='samplerate in Hz')
@click.option('--gain', '-g', type=float, default=30.0)
@click.option('--speed', '-s', type=int, default=4, help="determines the speed of the scanner, .i.e. the speed value is subtracted from the sampling time for each frequency")
@click.pass_context
def cli(ctx, samplerate, ppm, gain, speed):
    """
    IMSI catcher detector. This program tries to find nearby IMSI catchers using a RTL_SDR device.
    """
    if speed < 0 or speed > 5:
        print "Invalid scan speed.\n"
        raise click.Abort

    if (samplerate / 0.2e6) % 2 != 0:
        print "Invalid sample rate. Sample rate must be an even numer * 0.2e6"
        raise click.Abort

    ctx.obj['samplerate'] = samplerate
    ctx.obj['ppm'] = ppm
    ctx.obj['gain'] = gain
    ctx.obj['speed'] = speed

@click.command()
@click.option('--band', '-b', default="900M-Bands", help="select the band to scan. One of: E-GSM, P-GSM or R-GSM")
@click.option('--rec_time_sec', '-r', default=10, help='if the analyze option is specified, sets the recording time for each tower analysis in seocnds')
@click.option('--analyze' , '-a', is_flag=True, help='turns on anylis of each tower found of the scan. Will produce a capture file of each tower for duration specified with --rec_time_sec')
@click.option('--detection' , '-d', is_flag=True, help='if the analyze option is specified, turns on IMSI catcher detection during analysis of each tower')
@click.option('--location' , '-l', type=str, default='', help='current location used to mark a scan in Apple GPS minutes format')
@click.option('--lat', type=float, help='latitude used to specify the scan location, is used by detectors that perform location based detection of IMSI catchers')
@click.option('--lon', type=float, help='longitude used to specify the scan location, is used by detectors that perform location based detection of IMSI catchers')
@click.option('--unmute', '-u', is_flag=True, help='if the analyze option is specified, unmutes the output during analysis which will show the output of your capture device when it starts')
@click.pass_context
def scan(ctx, band, rec_time_sec, analyze, detection, location, lat, lon, unmute):
    """
    Scans for nearby cell towers and analyzes each cell tower and perfroms IMSI catcher detection if both are enabled.
    Note: if no location is specified, analysis of found towers is off
    :param detection: determines if druing analysis the packet based detectors are run
    """
    if band != "900M-Bands":
        if band not in grgsm.arfcn.get_bands():
            print "Invalid GSM band\n"
            return

    if band == "900M-Bands":
        to_scan = ['P-GSM',
                   'E-GSM',
                   'R-GSM',
                   #'GSM450',
                   #'GSM480',
                   #'GSM850',  Nothing found
                   'DCS1800', #BTS found with kal
                   'PCS1900', #Nothing interesting
                    ]
    else:
        to_scan = [band]


    args=ctx.obj

    try:
        loc = parse_dms(location)
        lat = loc[0]
        lon = loc[1]
    except:
        pass
    if lat is None or lon is None:
        print "Warning: no valid location specified. Cell tower consistency checks will be disabled in the analysis phase."

    if not analyze:
        print "Analysis of found towers is DISABLED. No online detection methods will be used."
    else:
        print "Analysis of found cell towers is ENABLED."
        if not detection:
            print "Online detection methods DISABLED."
    print "GSM bands to be scanned:\n"
    print "\t", "\n\t".join(to_scan)

    #Add scan to database
    #
    runner = Runner(bands=to_scan, sample_rate=args['samplerate'], ppm=args['ppm'], gain=args['gain'], speed=args['speed'], rec_time_sec=rec_time_sec, current_location=location)
    runner.start(lat, lon, analyze=analyze, detection=detection, mute=not unmute)

@click.command(help='Prints the saved scans')
@click.option('--limit', '-n', help='Limit the number of results returned', default=10)
@click.option('--printscans/--no-printscans', default=False)
def listScans(limit, printscans):
    lc(limit, printscans)

@click.command()
@click.option('--timeslot', default=0, type=int, help="Decode timeslot 0 - [timeslot]")
@click.option('--chan_mode', default='SDCCH8', help="Channel mode to demap the timeslots other than t0")
def detectOffline(chan_mode, timeslot):
    offlineDetection(chan_mode, timeslot)


@click.command()
@click.argument('filename', type=str)
@click.option('--sample_rate', default=2e6)
@click.option('--arfcn', default=1017)
@click.option('--timeslot', default=0, help="Decode timeslot 0 - [timeslot]")
@click.option('--chan_mode', default='SDCCH8', help="Channel mode to demap the timeslots other than t0")
def analyzeFile(filename, sample_rate, arfcn, timeslot, chan_mode):
    udp_port = 4729
    fa = FileAnalyzer(filename, sample_rate, arfcn, timeslot=timeslot, chan_mode=chan_mode, udp_port=udp_port, verbose=True, connectToSelf=True)
    fa.start()
    fa.wait()
    fa.stop()

@click.command()
def createdb():
    createDatabase()

if __name__ == "__main__":
    cli.add_command(scan)
    cli.add_command(listScans)
    cli.add_command(createdb)
    cli.add_command(analyzeFile)
    cli.add_command(detectOffline)
    cli(obj={})
