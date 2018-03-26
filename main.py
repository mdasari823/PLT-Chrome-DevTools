#!/usr/bin/env python3.5
__author__ = 'jnejati'

#import experiments
import json
import signal
import pickle
import webDnsSetup
import network_emulator
import os
import convert
from urllib.parse import urlparse
import time
#import modifications as modify
#from bs4 import BeautifulSoup
import urllib.request
import urllib.response
import io
import gzip
import subprocess
import logging
#import coloredlogs
#coloredlogs.install(level='INFO')
import timeit

def _change_resolv_conf():
    RESOLV_CONF = '/etc/resolv.conf'
    with open (RESOLV_CONF, 'w') as _f:
        _f.write('nameserver         127.0.0.1\n')


def main():
    start = timeit.default_timer()
    input_file = 'mixed_controlled.txt'
    archive_dir = '/home/jnejati/PLTSpeed/record/archive/'
    config_file = '/home/jnejati/PLTSpeed/confs/netProfiles.json'
    perf_args = '-etask-clock,context-switches,branches,branch-misses,cache-misses,cache-references,cycles:u,cycles:k,page-faults,sched:sched_switch,sched:sched_stat_runtime,sched:sched_wakeup,instructions:u,instructions:k,dTLB-load-misses,dTLB-loads,dTLB-store-misses,dTLB-stores,iTLB-load-misses,iTLB-loads,L1-dcache-load-misses,L1-dcache-loads,L1-dcache-stores,L1-icache-load-misses,LLC-load-misses,LLC-loads,LLC-store-misses,LLC-stores'
    _change_resolv_conf()
    with open(config_file, 'r') as f:
        net_profile = json.load(f)[0]
        _path =  os.path.join('/home/jnejati/PLTSpeed', net_profile['device_type'] + '_' + net_profile['name'])
        webDnsSetup.clear_folder(_path)
        #_google_chrome_stable = '/usr/bin/google-chrome-stable'
        #_remote_debugging_cmd = [_google_chrome_stable, '--remote-debugging-port=9222', '--start-maximized',  '--ignore-certificate-errors', '--user-data-dir=$TMPDIR/chrome-profiling', '--no-default-browser-check']
        #netns = network_emulator.NetworkEmulator(net_profile, dirs)
        #netns.set_profile(net_profile['conn_type'])
    with open('/home/jnejati/PLTSpeed/res/' + input_file) as _sites:
        for _site in _sites:
            #_chrome_process = subprocess.Popen(_remote_debugging_cmd)
            """os.system('pkill chrome')
            os.system('pkill google-chrome-stable')
            time.sleep(5)
            os.system('DISPLAY=:7 sudo google-chrome-stable --remote-debugging-port=9222 --start-maximized  --ignore-certificate-errors --user-data-dir=$TMPDIR/chrome-profiling --no-default-browser-check &')
            time.sleep(4)"""
            _site = _site.strip()
            logging.info('Navigating to: ' + _site)
            s1 = urlparse(_site)
            _site_data_folder = os.path.join(_path, s1.netloc)
            if not os.path.isdir(_site_data_folder):
                os.mkdir(_site_data_folder)
                os.mkdir(os.path.join(_site_data_folder, 'dns'))
            _d_ip_dict = webDnsSetup.setup_ip_subdomain(s1.netloc, archive_dir)
            webDnsSetup.setup_nameserver(_d_ip_dict)
            webDnsSetup.setup_webserver(s1.netloc, archive_dir, _d_ip_dict)
            for run_no in range(50):
                os.system('pkill chrome')
                os.system('pkill google-chrome-stable')
                time.sleep(5)
                os.system('DISPLAY=:7 sudo google-chrome-stable --remote-debugging-port=9222 --start-maximized  --ignore-certificate-errors --user-data-dir=$TMPDIR/chrome-profiling --no-default-browser-check &')
                time.sleep(5)
                _run_data_folder = os.path.join(_site_data_folder, 'run_' + str(run_no))
                if not os.path.isdir(_run_data_folder):
                    os.mkdir(_run_data_folder)
                    _subfolders = ['trace', 'screenshot', 'analysis', 'summary', 'tcpdump', 'perf']
                    for folder in _subfolders:
                        os.mkdir(os.path.join(_run_data_folder, folder))
                logging.info('Current profile: ' + net_profile['device_type'] + ' - ' + net_profile['name'] + ' run_no: ' + str(run_no) + ' site: ' + _site)
                #netns = network_emulator.NetworkEmulator(net_profile, dirs)
                #netns.set_profile(net_profile['conn_type'])
                os.system('pkill tcpdump')
                os.system('pkill node')
                time.sleep(15)
                _tcpdump_folder = os.path.join(_run_data_folder, 'tcpdump')
                _tcpdump_file = os.path.join(_tcpdump_folder, str(run_no) + '_' + s1.netloc)
                _tcpdump_cmd = ['tcpdump', '-i', 'lo', '-s', '0','-U', '-w', _tcpdump_file, 'not', 'port', '9222']
                _tcpdump_proc = subprocess.Popen(_tcpdump_cmd)
                _tcpdump_pid = str(_tcpdump_proc.pid)
                _perf_folder = os.path.join(_run_data_folder, 'perf')
                _perf_file = os.path.join(_perf_folder, str(run_no) + '_' + s1.netloc)
                _perf_cmd = ['perf', 'stat', '-x,', perf_args,  '--output', _perf_file, 'timeout', '--signal=SIGINT', '100'] 

                _trace_folder = os.path.join(_run_data_folder, 'trace')
                _screenshot_folder = os.path.join(_run_data_folder, 'screenshot')
                _summary_folder = os.path.join(_run_data_folder, 'summary')
                _trace_file = os.path.join(_trace_folder, str(run_no) + '_' + s1.netloc)
                _screenshot_file = os.path.join(_screenshot_folder, str(run_no) + '_' + s1.netloc)
                _summary_file = os.path.join(_summary_folder, str(run_no) + '_' + s1.netloc)
                logging.info(_trace_file, _screenshot_file, _summary_file)
                time.sleep(5)
                try:
                    _node_cmd = ['node', 'chrome_launcher.js', _site,  _trace_file, _summary_file, _screenshot_file, _tcpdump_pid]
                    _cmd = _perf_cmd + _node_cmd
                    subprocess.call(_cmd, timeout = 110)
                except subprocess.TimeoutExpired:
                    print("Timeout:  ", _site, run_no)
                    with open (os.path.join(_site_data_folder, 'log.txt'), 'w+') as _log:
                        _log.write("Timed out:  " +  _site + ' ' +  str(run_no) + '\n')
                time.sleep(15)
            pickle.dump(_d_ip_dict, open(os.path.join(_site_data_folder, 'dns/dnsBackup.txt'), 'wb'))
            time.sleep(2)
    stop = timeit.default_timer()
    #_chrome_process.kill()
    logging.info(100*'-' + '\nTotal time: ' + str(stop -start)) 
if __name__ == '__main__':
    main()
