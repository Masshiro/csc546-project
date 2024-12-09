import json
import time
import matplotlib.pyplot as plt
from typing import Dict, List, Optional
from src.helpers import run_with_mahi_settings, get_open_udp_port, generate_trace_file
from src.senders import Sender
from src.strategies import SenderStrategy, FixedWindowStrategy

TRACE_FILES = {
    '0.57MBPS': '0.57mbps-poisson.trace',
    '2.64MBPS': '2.64mbps-poisson.trace',
    '3.04MBPS': '3.04mbps-poisson.trace',
    '100.42MBPS': '100.42mbps.trace',
    '114.68MBPS': '114.68mbps.trace'
}

mahimahi_settings = {
    'delay': 88,
    'queue_size': 26400,
    'trace_file': TRACE_FILES['2.64MBPS']
}

# port = get_open_udp_port()
# run_with_mahi_settings(mahimahi_settings, 60, [Sender(port, FixedWindowStrategy(1000))])

generate_trace_file(10, './traces/low_10mbps.trace', 60)
generate_trace_file(30, './traces/med_30mbps.trace', 60)
generate_trace_file(100, './traces/high_100mbps.trace', 60)