import matplotlib.pyplot as plt
from subprocess import Popen
import socket
from threading import Thread
from typing import Dict, List
from src.senders import Sender

RECEIVER_FILE = "run_receiver.py"
AVERAGE_SEGMENT_SIZE = 80

def generate_mahimahi_command(mahimahi_settings: Dict) -> str:
    if mahimahi_settings.get('loss'):
        loss_directive = "mm-loss downlink %f" % mahimahi_settings.get('loss')
    else:
        loss_directive = ""
    return "mm-delay {delay} {loss_directive} mm-link traces/{trace_file} traces/{trace_file} --downlink-queue=droptail --downlink-queue-args=bytes={queue_size}".format(
      delay=mahimahi_settings['delay'],
      queue_size=mahimahi_settings['queue_size'],
      loss_directive=loss_directive,
      trace_file=mahimahi_settings['trace_file']
    )

def get_open_udp_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    s.bind(('', 0))
    port = s.getsockname()[1]
    s.close()
    return port

        
def print_performance(sender: Sender, num_seconds: int):
    print("Results for sender %d:" % sender.port)
    print("Total Acks: %d" % sender.strategy.total_acks)
    print("Num Duplicate Acks: %d" % sender.strategy.num_duplicate_acks)
    
    print("%% duplicate acks: %f" % ((float(sender.strategy.num_duplicate_acks * 100))/sender.strategy.total_acks))
    print("Throughput (bytes/s): %f" % (AVERAGE_SEGMENT_SIZE * (sender.strategy.ack_count/num_seconds)))
    print("Average RTT (ms): %f" % ((float(sum(sender.strategy.rtts))/len(sender.strategy.rtts)) * 1000))
    
    timestamps = [ ack[0] for ack in sender.strategy.times_of_acknowledgements]
    seq_nums = [ ack[1] for ack in sender.strategy.times_of_acknowledgements]

    plt.scatter(timestamps, seq_nums)
    plt.xlabel("Timestamps")
    plt.ylabel("Sequence Numbers")

    plt.show()
    
    plt.plot(sender.strategy.cwnds)
    plt.xlabel("Time")
    plt.ylabel("Congestion Window Size")
    plt.show()
    print("")
    
    if len(sender.strategy.slow_start_thresholds) > 0:
        plt.plot(sender.strategy.slow_start_thresholds)
        plt.xlabel("Time")
        plt.ylabel("Slow start threshold")
        plt.show()
    print("")
    
def run_with_mahi_settings(mahimahi_settings: Dict, seconds_to_run: int, senders: List):
    mahimahi_cmd = generate_mahimahi_command(mahimahi_settings)

    sender_ports = " ".join(["$MAHIMAHI_BASE %s" % sender.port for sender in senders])
    
    # cmd = "%s -- sh -c 'python3 %s %s'" % (mahimahi_cmd, RECEIVER_FILE, sender_ports)
    # receiver_process = Popen(cmd, shell=True)

    # discard all mahimahi outputs
    cmd = f"{mahimahi_cmd} -- sh -c 'python3 {RECEIVER_FILE} {sender_ports}' > /dev/null 2>&1"
    receiver_process = Popen(cmd, shell=True)

    for sender in senders:
        sender.handshake()
    threads = [Thread(target=sender.run, args=[seconds_to_run]) for sender in senders]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    
    for sender in senders:
        print_performance(sender, seconds_to_run)
    receiver_process.kill()

def generate_trace_file(bandwidth_mbps, output_file, duration_seconds):
    """
    Generate a Mahimahi trace file for a given bandwidth.

    Parameters:
    bandwidth_mbps (float): Desired bandwidth in Mbps.
    output_file (str): Output trace file name.
    duration_seconds (int): Duration of the trace in seconds.
    """
    # Constants
    mtu_bytes = 1500  # Size of an MTU packet in bytes
    mtu_bits = mtu_bytes * 8  # Size of an MTU packet in bits
    milliseconds_per_second = 1000  # Conversion factor for milliseconds

    # Calculate packets per millisecond
    packets_per_ms = bandwidth_mbps * 1e6 / mtu_bits / milliseconds_per_second

    # Open the output file for writing
    with open(output_file, "w") as f:
        current_time_ms = 0
        for _ in range(int(duration_seconds * milliseconds_per_second)):
            # Write timestamps based on packets per millisecond
            for _ in range(int(packets_per_ms)):
                f.write(f"{current_time_ms}\n")
            # Handle fractional packets
            if packets_per_ms % 1 > 0:
                fractional_chance = packets_per_ms % 1
                if fractional_chance > 0:
                    f.write(f"{current_time_ms}\n")
            current_time_ms += 1

    print(f"Trace file generated: {output_file}")
   