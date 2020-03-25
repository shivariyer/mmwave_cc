from mmparse import parse_mm_queue_delays, parse_mm_throughput 
import sys 
import matplotlib.pyplot as plt
import numpy as np

def plot_tput_delay(filepath, ms_per_bin=500):
    
    delays, delaytimes = parse_mm_queue_delays(filepath)
    print('Max delay:', max(delays))
    print('Min delay:', min(delays))
    print('Avg delay:', sum(delays) / len(delays))

    ms_elapsed, data = parse_mm_throughput(filepath, ms_per_bin)
    print(data.index)
    #timeDL, caps, arr, throughputDL = parse_tcp_throughput(file_to_plot)
    
    fig = plt.figure(figsize=(6,3), facecolor='w')
    ax1 = plt.subplot(2, 1, 1)
    ax2 = plt.subplot(2, 1, 2, sharex=ax1)

    labels = ['Capacity','Arrivals','Throughput']
    p3, = ax2.plot(delaytimes, delays,'k-',lw=1, label="Delay")
    #ax1.plot(data.index, data.capacity,'k-',lw=1,label=labels[0])
    p2 = ax1.fill_between(data.index, 0, data.capacity,color='#F2D19F',label="Capacity")

    #ax1.plot(data.index, data.arrival,'k-',label=labels[1])
    p1, = ax1.plot(data.index, data.departure,'k--',label=labels[2])

    print('Avg utilization:', np.ma.masked_invalid(np.divide(data.departure, data.capacity)).mean() * 100)

    box = ax1.get_position()
    ax1.set_position([box.x0, box.y0 + box.height * 0.1,
                 box.width, box.height * 0.9])
    ax1.legend((p1, p2, p3), (p1.get_label(), p2.get_label(), p3.get_label()), loc='upper center', bbox_to_anchor=(0.5, 1.4), ncol=5, fontsize="small")
    
    ax1.set_ylabel("Mbps")
    ax2.set_ylabel("Delay (ms)")
    plt.xlabel("Time (sec)")
    
    #plt.xlim(0,60)
    plt.tight_layout()
    #plt.savefig(name.split('.')[0]+'.pdf',dpi=1000,bbox_inches='tight')
    plt.show()
    plt.close()


if __name__ == '__main__':

    if len(sys.argv) < 2:
        print('Usage: {} <mm_log_file>'.format(sys.argv[0]))
        sys.exit(-1)
    
    plot_tput_delay(sys.argv[1])
