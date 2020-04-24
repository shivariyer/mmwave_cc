
import os
import sys
import argparse
import numpy as np
import pandas as pd

from tqdm import tqdm
from utils import prettyprint_args

def prepare_dataset_join(df_input, df_output, nhist, nagg=1):
    '''Revamped and simpler (and hopefully also faster) implementation
    utilizing in-built "join" function for joining two dataframes.
    
    '''

    df_joined = df_input.join(df_output, on='unix_time_ms', how='inner')
    df_joined.dropna(inplace=True) # remove rows that have NaNs
    df_joined.loc[np.isinf(df_joined.qfrac_cap.values), 'qfrac_cap'] = 0 # replace "inf"s with zeros

    colnames_set = ['RTT_s', 'IAT1_us', 'delay_s', 'IAT2_us', 'qfrac', 'qfrac_cap', 'capacity']
    
    nrows = df_joined.shape[0] - nhist
    ncols = len(colnames_set) * (nhist + 1)
    dataset = np.empty((nrows, ncols))

    # TODO: it is important that order of packets in df_input be the
    # actual order of arrival of respective acks for packets at the
    # sender. This might not be the case, so need to check that.
    subdf = df_joined[colnames_set]
    for k in tqdm(range(nrows)):
        dataset[k,:] = subdf.iloc[k:k+nhist+1].values.ravel()
    
    colnames_list = []
    for i in reversed(range(nhist+1)):
        suf = 'tminus{}'.format(i)
        colnames_list.extend(['RTT_' + suf, 'IAT1_' + suf, 'delay_' + suf, 'IAT2_' + suf, 'Qfrac_' + suf, 'QfracCap_' + suf, 'Cap_' + suf])
    dataset_df = pd.DataFrame(dataset, columns=colnames_list)
    
    return dataset_df


def prepare_dataset(df_input, df_output, histlen):
    
    dataset = []
    
    # for i in tqdm(range(df_input.index.size-histlen)):
    #     inputfeatures = df_input.iloc[i:i+histlen+1].Delay
    #     outputlabel = df_output.iloc[i+histlen].smaller_congestion
    #     if inputfeatures.count() == histlen+1 and not np.isnan(outputlabel):
    #         dataset.append(inputfeatures.tolist() + [outputlabel])
    
    start_ts = df_output.index[0]
    
    df_input['Serial'] = np.arange(1, df_input.shape[0] + 1)
    df_input['qfrac'] = np.empty(df_input.shape[0]) * np.nan
    df_input['qfrac_cap'] = np.empty(df_input.shape[0]) * np.nan
    df_input['capacity'] = np.empty(df_input.shape[0]) * np.nan
    
    # first add column for ecn_bit
    for ts, qfrac, qfrac_cap, cap in df_output[['qfrac', 'qfrac_cap', 'capacity']].itertuples():
        if ts in df_input.index:
            df_input.loc[ts,'qfrac'] = qfrac
            df_input.loc[ts,'qfrac_cap'] = qfrac_cap
            df_input.loc[ts,'capacity'] = cap
    
    for i in tqdm(range(df_output.index.size)):
        # for every point in the output table, check if all input
        # features and output labels are available, and if so, add
        # the feature vector and output label to the dataset
        tup = df_output.iloc[i]
        
        # if not np.isnan(tup.smaller_congestion) and not np.isnan(tup.ecn_bit):
        #     ts = tup.name
        #     pkts_hist = []
        #     k = 0
        #     while k != histlen and ts >= start_ts:
        #         ts -= 1
        #         if ts in df_input.index:
        #             if not any(np.isnan(df_input.loc[ts].Delay.values)) and not np.isnan(df_output.loc[ts].smaller_congestion) and not np.isnan(df_output.loc[ts].ecn_bit):
        #                 k += 1
        #                 # pkts_hist.append((tup.Index - ts, df_input.loc[ts].Delay.values, df_output.loc[ts].smaller_congestion, df_output.loc[ts].ecn_bit))
        #                 pkts_hist.append((tup.name - ts, df_input.loc[ts].Delay.values, df_output.loc[ts].smaller_congestion, df_output.loc[ts].ecn_bit))
        
        #     if k == histlen:
        #         # if all historical values were available, then
        #         # build the feature vector and put it along with
        #         # the output label in the dataset
        
        #         # (1) take average of all delays in that millisecond
        #         inputfeatures = []
        #         for ftup in pkts_hist:
        #             inputfeatures.extend([ftup[0], ftup[1].mean(), ftup[3]])
        #         dataset.append(inputfeatures + [tup.ecn_bit])
        
        ts = tup.name
        
        if ts in df_input.index:
            i_start, i_end = df_input.loc[ts].Serial.iloc[0], df_input.loc[ts].Serial.iloc[-1] + 1
            subdf = df_input.iloc[i_start-histlen:i_end]
            for k in range(subdf.shape[0]-histlen):
                feature_vector = subdf[['RTT_s', 'IAT_s', 'qfrac', 'qfrac_cap', 'capacity']].iloc[k:k+histlen+1].values.ravel()
                if np.isfinite(feature_vector).all():
                    #feature_vector = np.append(feature_vector, tup.capacity)
                    dataset.append(feature_vector)
    
    dataset = np.asarray(dataset)
    
    # ','.join(['arrivaltime_tminus{0:02d},avgdelay_tminus{0:02d},ecn_tminus{0:02d}'.format(i) for i in reversed(range(1,histlen+1))]) + ',ecn'
    colnames = []
    for i in reversed(range(0, histlen+1)):
        suf = 'tminus{}'.format(i)
        # colnames.extend(['arrivaltime_' + suf, 'avgdelay_' + suf, 'ecn_' + suf])
        #colnames.extend(['RTT_' + suf, 'IAT_' + suf, 'CM_' + suf])
        colnames.extend(['RTT_' + suf, 'IAT_' + suf, 'Qfrac_' + suf, 'QfracCap_' + suf, 'Cap_' + suf])
    # colnames.append('CM')
    #colnames.extend(['Cap_tminus0'])
    dataset_df = pd.DataFrame(dataset, columns=colnames)
    
    return dataset_df



if __name__ == '__main__':
    
    # features to use in prediction may be current and historical
    # per-packet delays, current and historical value of congestion
    # and ECN, and rate of change of delays (diff delay over time)
    
    parser = argparse.ArgumentParser(description="part of testbed code for experimenting with algos to predict congestion")
    # parser.add_argument('trace', metavar='TRACE', help="trace name") # 
    # parser.add_argument('keyword', metavar='KEYWORD', help="keyword to help find the right input files")
    # parser.add_argument('--algo', '-a', help="The specific algo",
    #     	        default='udp')
    # parser.add_argument('--direction', '-d', help="Whether to use uplink or downlink trace",
    #     	        default='uplink')
    parser.add_argument('--filespec', required=True, metavar='FILESPEC', dest='filespeclist',
                        action='append', help="Suffix string to locate the right input files (in input folder)")
    parser.add_argument('--history', required=True, type=int, help="Length of history to use in predictor (H)")
    parser.add_argument('--outnamesuffix', '-o', required=True, help="Suffix for output dataset file name")
    # parser.add_argument('--ahead', type=int, help="How far in future must we attempt to predict", default=1)
    parser.add_argument('--ifolder', '-if', help="Folder where the files are (mmcongestion_*, avgdelaysmilli_*, pktdelays_*)", default='analysis')
    parser.add_argument('--ofolder', '-of', help="Folder where to export output dataset", default='datasets')
    parser.add_argument('--yes', '-y', action='store_true', help="Answer yes to prompt")
    args = parser.parse_args()
    
    prettyprint_args(args)
    
    # first check if we need to create the dataset file in the first
    # place
    dpath = os.path.join(args.ofolder, 'dataset_H{:02d}_{}.csv'.format(args.history, args.outnamesuffix))
    
    if not args.yes and os.path.exists(dpath):
        inp = input('Dataset file \'{}\' already exists! Overwrite? [y/Y to proceed] '.format(dpath))
        inp = inp.strip().lower()
        
        if inp != 'y':
            print('Aborting.')
            sys.exit(-2)
    
    # read in the outputs of plotqueuesize script required to prepare
    # the dataset
    errormsg = 'Required file \"{}\" not present. Please run \"plotqueuesize.py\" with similar commandline arguments to generate it and then run this again.'
    
    dataset_df_list = []
    
    for filenamesuffix in args.filespeclist:
        
        dpath_this = os.path.join(args.ofolder, 'dataset_H{:02d}_{}.csv'.format(args.history, filenamesuffix))
        if os.path.exists(dpath_this):
            dataset_df = pd.read_csv(dpath_this)
            
        else:
            
            # table containing output labels to predict (i.e. the congestion labels)
            filepath = os.path.join(args.ifolder, 'mmcongestion_{}.csv'.format(filenamesuffix))
            if not os.path.exists(filepath):
                print(errormsg.format(filepath), file=sys.stderr)
                sys.exit(-1)
            df_output = pd.read_csv(filepath, index_col=[0])
            
            # table containing input features (i.e. the computed delays)
            # filepath = os.path.join(args.ifolder, 'avgdelaysmilli_{}.csv'.format(filenamesuffix))
            filepath = os.path.join(args.ifolder, 'pktdelays_{}.csv'.format(filenamesuffix))
            if not os.path.exists(filepath):
                print(errormsg.format(filepath), file=sys.stderr)
                sys.exit(-1)
            # df_input = pd.read_csv(filepath, index_col=[0])
            df_input = pd.read_csv(filepath, index_col=[0,1])
            
            # now generate the dataset (if not already present)
            #dataset_df = prepare_dataset(df_input, df_output, args.history)
            dataset_df = prepare_dataset_join(df_input, df_output, args.history)
        
        dataset_df_list.append(dataset_df)
    
    # concatenate all datasets to create master datasets
    dataset_df_all = pd.concat(dataset_df_list, ignore_index=True, sort=False, copy=False)
    
    # finished reading in the dataset
    print('Number of available points in dataset:', dataset_df_all.shape[0])
    print('Dimensionality of input features:', dataset_df_all.shape[1] - 1)
    # print('Dimensionality of output labels: ', args.ahead)
    
    # save the dataset
    
    # fout = open(, 'w')
    # fout.write(','.join(['avgdelay_tminus{:02d}'.format(i) for i in reversed(range(histlen+1))]) + ',congestion_label' + os.linesep)
    # fout.write( + os.linesep)
    # np.savetxt(fout, dataset, delimiter=',', fmt='%f')
    # fout.close()
    
    if not os.path.exists(args.ofolder):
        os.mkdir(args.ofolder)
    
    dataset_df_all.to_csv(dpath, index=False)
