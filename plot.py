from mmparse import parse_tcp_delays
from mmparse import parse_tcp_throughput 
import sys 
import matplotlib.pyplot as plt
import numpy as np
#python plot.py filename 


def plotindividual(delays,delaytimes,timeDL,caps,arr,throughputDL,name):

    fig = plt.figure(figsize=(6,3), facecolor='w')
    ax1 = plt.subplot(2, 1, 1)
    ax2 = plt.subplot(2, 1, 2, sharex=ax1)

    labels = ['Capacity','Arrivals','Throughput']
    p3, = ax2.plot(delaytimes, delays,'k-',lw=1, label="Delay")
    #ax1.plot(timeDL, caps,'k-',lw=1,label=labels[0])
    p2 = ax1.fill_between(timeDL, 0, caps,color='#F2D19F',label="Capacity")

    #ax1.plot(timeDL, arr,'k-',label=labels[1])
    p1, = ax1.plot(timeDL, throughputDL,'k--',label=labels[2])

    print 'Avg utilization:', np.ma.masked_invalid(np.divide(throughputDL, caps)).mean() * 100

    box = ax1.get_position()
    ax1.set_position([box.x0, box.y0 + box.height * 0.1,
                 box.width, box.height * 0.9])
    ax1.legend((p1, p2, p3), (p1.get_label(), p2.get_label(), p3.get_label()), loc='upper center', bbox_to_anchor=(0.5, 1.4), ncol=5, fontsize="small")

    ax1.set_ylabel("Mbps")
    ax2.set_ylabel("Delay (ms)")
    plt.xlabel("Time (sec)")
    
    plt.xlim(0,60)
    plt.tight_layout()
    #plt.savefig(name.split('.')[0]+'.pdf',dpi=1000,bbox_inches='tight')
    plt.show()
    plt.close()


file_to_plot = sys.argv[1]

delays2, delayTimes2 = parse_tcp_delays(file_to_plot)
timeDL, caps, arr, throughputDL = parse_tcp_throughput(file_to_plot)
plotindividual(delays2,delayTimes2,timeDL,caps,arr,throughputDL,file_to_plot)




