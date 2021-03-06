#!/usr/bin/python3
##
## qitime - Quality Imaging Time
## (C) 2020 Victor R. Ruiz <rvr@linotipo.es>
##
## Calculates the Quality Imaging Time (dark hours) for a given date.
## Based on a concept developed by Charles Bracken:
## https://digitalstars.wordpress.com/
##
import argparse
import datetime
import ephem

def quality_time(
    date_time,
    latitude,
    longitude,
    moon_display=False,
    debug=False,
    header=False,
    ):
    """ Calculate quality time. """
    ## Observer data
    observer = ephem.Observer()
    observer.lon = latitude
    observer.lat = longitude
    observer.elevation = 0
    observer.pressure = 1013 # USNO
    observer.temp = 10
    observer.horizon = '-0:34' # USNO
    observer.date = date_time # Local time

    if debug:
        print("= Observer")
        print("  Date:{}\tLon:{}\tLat:{}".format(
            observer.date,
            observer.lon,
            observer.lat
        ))

    ## Objects
    sun = ephem.Sun()
    moon = ephem.Moon()
    # Compute 
    sun.compute(observer)
    moon.compute(observer)
    # Calculate moon phase
    next_new_moon = ephem.next_new_moon(observer.date)
    prev_new_moon = ephem.previous_new_moon(observer.date)
    # 50 = full moon, 0 = new moon
    lunation = (observer.date - prev_new_moon) / (next_new_moon - prev_new_moon) * 100

    objects = { 'Sun': sun, 'Moon': moon }
    times = {}

    if debug: print("= Rise/Transit/Set")
    for target in objects:
        t = objects[target]
        times[target] = {
            'rise' : None,
            'transit' : None,
            'set' : None,
            'always_up': False,
            'never_up': False,
        }
        try:
            times[target]['rise'] = ephem.localtime(observer.next_rising(t, use_center=True))
            times[target]['transit'] = ephem.localtime(observer.next_transit(t))
            times[target]['set'] = ephem.localtime(observer.next_setting(t, use_center=True))
            if debug:
                print("  {}\tRise:{}\tTransit:{}\tSet:{}".format(
                    target,
                    times[target]['rise'],
                    times[target]['transit'],
                    times[target]['set']
                ))
        except ephem.AlwaysUpError:
            if debug: print("  {} always up".format(target))
            times[target]['always_up'] = True
        except ephem.NeverUpError:
            if debug: print("  {} never up".format(target))
            times[target]['never_up'] = True

    ## Twilight
    # https://stackoverflow.com/questions/2637293/calculating-dawn-and-sunset-times-using-pyephem
    # fred.horizon = '-6' #-6=civil twilight, -12=nautical, -18=astronomical
    if debug: print("= Twilight")
    twilight = {
        #'Civil': '-6',
        #'Nautical': '-12',
        'Quality': '-15',
        #'Astronomical': '-18'
        }
    for twilight_type in twilight:
        observer.horizon = twilight[twilight_type]
        dawn_t = "{}_dawn".format(twilight_type)
        dusk_t = "{}_dusk".format(twilight_type)
        always_t = "{}_always".format(twilight_type)
        never_t = "{}_never".format(twilight_type)
        times[dawn_t] = None
        times[dusk_t] = None
        times[always_t] = False
        times[never_t] = False
        try:
            # Calculate twilight times
            times[dusk_t] = ephem.localtime(observer.next_setting(sun, use_center=True))
            times[dawn_t] = ephem.localtime(observer.next_rising(sun, use_center=True))
            if debug:
                print("  {}\tDawn:{}\tDusk:{}".format(
                    twilight_type,
                    times[dusk_t],
                    times[dawn_t]
                ))
        except ephem.AlwaysUpError:
            times[always_t] = True
            if debug: print("  There is not {} night".format(twilight_type))
        except ephem.NeverUpError:
            times[never_t] = True
            if debug: print("  There is not {} night".format(twilight_type))

    ## Dark Night
    if debug: print("= Dark night (without any Moon)")
        # Calculate limits
    for twilight_type in twilight:
        dawn_t = "{}_dawn".format(twilight_type)
        dusk_t = "{}_dusk".format(twilight_type)
        always_t = "{}_always".format(twilight_type)
        never_t = "{}_never".format(twilight_type)
        if debug:
            print("  Darkness ({})\tStart:{}\tEnd:{}".format(
                twilight_type,
                times[dusk_t],
                times[dawn_t]
            ))
        dt = observer.date.datetime()
        if debug:
            print("  ", end='')
            for i in range(0,24):
                    print("{:02}  ".format(i), end='')
            print(" Moon phase")
        print("  ", end='')
        phase = ""
        if lunation < 6.25 or lunation > 93.75:
            phase = "🌑"
        elif lunation < 18.75:
            phase = "🌒"
        elif lunation < 31.25:
            phase = "🌓"
        elif lunation < 43.75:
            phase = "🌔"
        elif lunation < 56.25:
            phase = "🌕"
        elif lunation < 68.75:
            phase = "🌖"
        elif lunation < 81.25:
            phase = "🌗"
        elif lunation <= 93.75:
            phase = "🌘"
        for h in range(0,24):
            for m in [0, 30]:
                current_date = ephem.localtime(ephem.Date("{}-{}-{} {:02d}:{:02d}:00".format(
                    dt.year,
                    dt.month,
                    dt.day,
                    h,
                    m
                )))
                if times[always_t]:
                    print("🌞", end='')
                elif times[never_t] == False \
                    and current_date > times[dawn_t] \
                    and current_date < times[dusk_t]:
                    print("🌞", end='')
                else:
                    if moon_display == True:
                        observer.horizon = "0"
                        observer.date = current_date
                        moon.compute(observer)
                        if moon.alt > 0:
                            print(phase, end='')
                        else:
                            print("🌌", end='')
                    else:
                        print("🌌", end='')
        print(" {}".format(phase))


if (__name__ == '__main__'):
    # Parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--lat", help="Observer latitude", required=True)
    parser.add_argument("--lon", help="Observer longitude", required=True)
    parser.add_argument("--date", help="Date to calculate ephemeris", required=True)
    args = parser.parse_args()

    # Display header
    print("Quality Imaging Time")
    # Calculate and display Quality Imaging ephemeris
    quality_time(
        args.date,
        latitude=args.lat,
        longitude=args.lon,
        debug=True,
        moon_display=True,
        header=True,
    )
    # TODO: Calendar
    """
    header_display = True
    for week in range(0,52):
        for day in [4,5,6]:
            # Friday, Saturday
            date = datetime.datetime.strptime('2020 {} {}'.format(week, day), '%Y %U %w')
            date_str = "2020-{:02}-{:02} 00:00".format(date.month, date.day)
            print("2020-{:02}-{:02}".format(date.month, date.day), end='')
            quality_time(
                date_str,
                latitude=args.lat,
                longitude=args.lon,
                debug=False,
                moon_display=True,
                header=header_display
            )
            if header_display == True:
                header_display = False
    """

