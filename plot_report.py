import os
import re
import glob
import math
import matplotlib as mpl
#mpl.use('Agg')
import matplotlib.pyplot as plt

if __name__ == '__main__':
    inpdir = "results/clustering_202005201231"

    curr_hist = 0
    MAX_hist = 10
    if True:
    #for curr_hist in range(MAX_hist+1):

        pat = re.compile('(fset(\d+)_thres(\d+)_H\d+_(.+)_pkt(\d{2})_s(.+))\.')

        allfiles = glob.glob(os.path.join(inpdir, f'report_*_H{curr_hist}_*.txt'))
        allfiles.sort()

        curr_fset = '0'
        #pkt_aggr = [1, 5, 10, 20, 30, 40, 50]
        pkt_aggr = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        stats = {
            "fanrunning": {'0': [], '1': [], '2': []},
            "humanmotion": {'0': [], '1': [], '2': []},
            "stationary": {'0': [], '1': [], '2': []},
            "walkandturn": {'0': [], '1': [], '2': []}
        }

        for fpath in allfiles:
            fname = os.path.basename(fpath)
            m = pat.search(fname)
            fsuffix, fset, thres, tracename, npkts, s = m.groups()

            with open(os.path.join(inpdir, f'report_{fsuffix}.txt')) as report_fp:
                for line in report_fp:
                    line_list = line.split()
                    if line_list: # skip line of its empty
                        if line_list[0] == "macro":
                            # append accuracy's f1 score
                            f1_score = float(line_list[4])
                            stats[tracename][fset].append(f1_score)
                            break


        traces = ["fanrunning", "humanmotion", "stationary", "walkandturn"]
        print("===============================")
        for trace in traces:
            # print(f"{trace} with history {curr_hist}")
            # #print(stats[trace])
            # max_score = [-math.inf, '', -1]
            # for fset in stats[trace].keys():
            #     for i, score in enumerate(stats[trace][fset]):
            #         if score > max_score[0]:
            #             max_score[0] = score
            #             max_score[1] = fset
            #             max_score[2] = pkt_aggr[i]
            # print(max_score)

            plt.plot(pkt_aggr, stats[trace]['0'], 'rs')
            plt.plot(pkt_aggr, stats[trace]['0'], 'r')
            plt.plot(pkt_aggr, stats[trace]['1'], 'bo')
            plt.plot(pkt_aggr, stats[trace]['1'], 'b')
            plt.plot(pkt_aggr, stats[trace]['2'], 'g^')
            plt.plot(pkt_aggr, stats[trace]['2'], 'g')
            plt.axis([0,10,0,1])
            plt.xlabel('Packet Aggregation')
            plt.ylabel('f1 Score')
            plt.title(f'Trace: {trace}; History: {curr_hist}')
            plt.show()

    



        # for each fset make a graph
