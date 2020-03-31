#!/usr/bin/env python3

import argparse
import os
import sys
import traceback
from datetime import datetime
from time import sleep
import pytz
import logging
import dateutil
from dateutil.parser import parse

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Rate of increase of covid cases in Switzerland',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--dir_path', dest='dir_path', default='../fallzahlen_kanton_total_csv/', help='Alpha vantage API key')
    args = parser.parse_args()
    log_level = logging.INFO
    logging.basicConfig(format='%(asctime)s %(message)s', level=log_level,
                        datefmt='%Y-%m-%d %H:%M:%S')

    '''
date,time,abbreviation_canton_and_fl,ncumul_tested,ncumul_conf,ncumul_hosp,ncumul_ICU,ncumul_vent,ncumul_released,ncumul_deceased,source
2020-02-27,13:00,BS,2,1,0,,,,,https://www.coronavirus.bs.ch
2020-02-27,17:13,FL,2,1,1,,,,,https://www.regierung.li/media/attachments/83-verdachtsfaelle-negativ-getestet.pdf?t=637202562374055719
    '''
    pwd=os.path.join(os.getcwd(),args.dir_path)
    nfiles=0
    # Not all cantons have updated info per day, so keep track of all unique dates
    all_dts=[]
    # sum per canton per date
    date_to_cnt_sum={}
    for fname in os.listdir(pwd):
        if not fname.endswith('CH_total.csv'):
            continue
        fn=os.path.join(pwd, fname)
        with open(fn, 'r', encoding='utf-8') as f:
            logging.debug('opening file {}'.format(fn))
            next(f)                # skip first line
            dt=parse('2001-01-01') # init to invalid
            try:
                for line in f:
                    try:
                        new_cumul_pos=int(line.split(',')[4])
                    except:
                        continue
                    new_dt = parse(line.split(',')[0])
                    cnt=line.split(',')[2]
                    if cnt not in date_to_cnt_sum:
                        date_to_cnt_sum[cnt]={}
                    #if new_dt == dt:
                    #    logging.error('Two rows with the same date prev={} new={}'.format(dt, new_dt))
                    dt=new_dt
                    date_to_cnt_sum[cnt][dt]=new_cumul_pos
                    if dt not in all_dts:
                        all_dts.append(dt)
            except Exception:
                exc_type, exc_value, exc_traceback = sys.exc_info()
                traceback.print_exception(exc_type, exc_value, exc_traceback,
                                          limit=2, file=sys.stdout)
                logging.info('error at line={}'.format(line))
                sys.exit(1)
        nfiles+=1
    # total sums per date
    date_to_sum={}
    # total update counts per date (how many cantons provided update on that date)
    date_update_cnt={}
    # go over all dates in sorted order
    sdts=sorted(all_dts)
    for dt in sdts:
        date_to_sum[dt]=0
        date_update_cnt[dt]=0
        for cnt in date_to_cnt_sum.keys():
            val=0
            for cdt in sorted(date_to_cnt_sum[cnt].keys()):
                if cdt <= dt:
                    val=date_to_cnt_sum[cnt][cdt]
                if cdt == dt:
                    date_update_cnt[dt]+=1
            logging.debug('cnt={} val={} date={}'.format(cnt, val, dt))
            date_to_sum[dt]+=val
    skeys=sorted(date_to_sum.keys())
    for key in skeys:
        logging.debug('date={} sum={}'.format(key, date_to_sum[key]))

        # remove dates without full info
    #    if date_update_cnt[key] != nfiles:
    #        date_to_sum.pop(key, None)
    #        logging.info('incomplete date for date={} files={} upds={}'.format(key, nfiles, date_update_cnt[key]))
    skeys=sorted(date_to_sum.keys())
    diffs=[]
    prev=0
    for key in skeys:
        logging.debug('date={} prev={} cur={}'.format(key, prev, date_to_sum[key]))
        assert date_to_sum[key] >= prev
        diffs.append(date_to_sum[key] - prev)
        prev=date_to_sum[key]
    logging.debug('lastd={} lastv={}'.format(skeys[-1], diffs[-1]))
    logging.info('sum={}'.format(sum(diffs)))
    import matplotlib.pyplot as plt
    # print(len(skeys))
    # print(len(diffs))
    # print(len(date_to_cnt_sum))
    # fig = plt.figure()
    # plt.plot_date(skeys, diffs, 'g-', secondary_y=True)
    # plt.plot_date(skeys, [date_update_cnt[dt] for dt in skeys], 'b-')
    # plt.show()


    fig, ax1 = plt.subplots()

    color = 'tab:red'
    ax1.set_xlabel('date')
    ax1.set_ylabel('covid-19 incident increase from previous day', color=color)
    ax1.bar(skeys, diffs, color=color)
    ax1.tick_params(axis='y', labelcolor=color)

    ax2 = ax1.twinx()  # instantiate a second axes that shares the same x-axis

    color = 'tab:blue'
    ax2.set_ylabel('# cantons reported (out of 27)', color=color)  # we already handled the x-label with ax1
    ax2.plot(skeys, [date_update_cnt[dt] for dt in skeys], color=color)
    ax2.tick_params(axis='y', labelcolor=color)
    ax2.set_ylim(0, 27)
    fig.tight_layout()  # otherwise the right y-label is slightly clipped

    fig2 = plt.figure(2)
    color = 'tab:red'
    ax3 = fig2.add_subplot(111)
    ax3.set_ylabel('total number of incidents')
    ax3.bar(skeys, [date_to_sum[dt] for dt in skeys], color=color)

    plt.show()
