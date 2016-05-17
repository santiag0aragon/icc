from icc.runner import Runner, createDatabase
from icc.runner import listScans as lc
from icc.aux.lat_log_utils import parse_dms
import grgsm
import click

@click.group()
@click.option('--ppm', '-p', default=0)
@click.option('--samplerate', '-sr', default=2e6, type=float)
@click.option('--gain', '-g', type=float, default=30.0)
@click.option('--speed', '-s', type=int, default=4)
@click.pass_context
def cli(ctx, samplerate, ppm, gain, speed):
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
@click.option('--band', '-b', default="900M-Bands")
@click.option('--rec_time_sec', '-r', default=10)
@click.option('--analyze' , '-a', is_flag=True)
@click.option('--detection' , '-d', is_flag=True)
@click.option('--location' , '-l', type=str, default='')
@click.option('--lat', type=float)
@click.option('--lon', type=float)
@click.pass_context
def scan(ctx, band, rec_time_sec, analyze, detection, location, lat, lon):
    """
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
                   #'DCS1800', #BTS found with kal
                   #'PCS1900', #Nothing interesting
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


    print "GSM bands to be scanned:\n"
    print "\t", "\n\t".join(to_scan)

    #Add scan to database
    #
    runner = Runner(bands=to_scan, sample_rate=args['samplerate'], ppm=args['ppm'], gain=args['gain'], speed=args['speed'], rec_time_sec=rec_time_sec, current_location=location)
    runner.start(lat, lon, analyze=analyze, detection=detection)

@click.command(help='Prints the saved scans')
@click.option('--limit', '-n', help='Limit the number of results returned', default=10)
@click.option('--printscans/--no-printscans', default=False)
def listScans(limit, printscans):
    lc(limit, printscans)

@click.command()
def createdb():
    createDatabase()

if __name__ == "__main__":
    cli.add_command(scan)
    cli.add_command(listScans)
    cli(obj={})
