import os
from io import StringIO
from datetime import datetime
from obspy import UTCDateTime
from obspy.clients.fdsn import Client

import pandas as pd
import matplotlib.pyplot as plt

def search_target(base_url, station, start_time, end_time, confidence_threshold = 0.7):
    # --- load catalog ---
    url = f"{base_url}query?tid=BG.{station}.&start_time={start_time}&end_time={end_time}&limit=10000"

    df_picks = pd.read_csv(url, delimiter="|")
    print(df_picks.head())
    # print(df_picks.tail())

    p_start_time = df_picks.loc[df_picks["phase"] == "P", "start_time"].tolist()
    p_peak_time = df_picks.loc[df_picks["phase"] == "P", "peak_time"].tolist()
    p_end_time = df_picks.loc[df_picks["phase"] == "P", "end_time"].tolist()
    p_confidence = df_picks.loc[df_picks["phase"] == "P", "confidence"].tolist()

    s_start_time = df_picks.loc[df_picks["phase"] == "S", "start_time"].tolist()
    s_peak_time = df_picks.loc[df_picks["phase"] == "S", "peak_time"].tolist()
    s_end_time = df_picks.loc[df_picks["phase"] == "S", "end_time"].tolist()
    s_confidence = df_picks.loc[df_picks["phase"] == "S", "confidence"].tolist()

    p_start_time = pd.to_datetime(p_start_time)
    p_peak_time = pd.to_datetime(p_peak_time)
    p_end_time = pd.to_datetime(p_end_time)
    s_start_time = pd.to_datetime(s_start_time)
    s_peak_time = pd.to_datetime(s_peak_time)
    s_end_time = pd.to_datetime(s_end_time)

    print(len(p_start_time), len(p_peak_time), len(p_end_time), len(p_confidence))
    print(len(s_start_time), len(s_peak_time), len(s_end_time), len(s_confidence))

    warning_num = 0
    if (len(p_start_time) > 9999) or (len(s_start_time) > 9999):
        print("Warning: The number of picks has reached the limit of 10,000. Consider narrowing the time window to avoid missing data.")
        print(f"Redo case: {station}, {start_time}, {end_time}")
        warning_num = 1


    # --- Find pairs of P and S picks that are close in time (within 5 seconds) and where the P pick occurs before the S pick ---
    p_pair_id = []
    s_pair_id = []

    for i, p_time in enumerate(p_peak_time):
        for j, s_time in enumerate(s_peak_time):
            if abs(s_time - p_time).total_seconds() < 5 and (p_time < s_time):
                p_pair_id.append(i)
                s_pair_id.append(j)

    # --- search for single P and S picks that do not have a corresponding pair within 5 seconds ---
    p_single = []
    p_single_id = []
    p_single_confidence = []

    p_single_worth_checking = []
    p_single_worth_checking_confidence = []

    s_single = []
    s_single_id = []
    s_single_confidence = []

    s_single_worth_checking = []
    s_single_worth_checking_confidence = []

    p_log = ['p_start_time,p_peak_time,p_end_time,confidence']
    s_log = ['s_start_time,s_peak_time,s_end_time,confidence']

    for i in range(len(p_peak_time)):
        if i not in p_pair_id:
            p_single_id.append(i)
            p_single.append(p_peak_time[i])
            p_single_confidence.append(p_confidence[i])
            if p_confidence[i] > confidence_threshold:
                p_log.append(f"{p_start_time[i]},{p_peak_time[i]},{p_end_time[i]},{p_confidence[i]}")
                p_single_worth_checking.append(p_peak_time[i])
                p_single_worth_checking_confidence.append(p_confidence[i])

    for j in range(len(s_peak_time)):
        if j not in s_pair_id:
            s_single_id.append(j)
            s_single.append(s_peak_time[j])
            s_single_confidence.append(s_confidence[j])
            if s_confidence[j] > confidence_threshold:
                s_log.append(f"{s_start_time[j]},{s_peak_time[j]},{s_end_time[j]},{s_confidence[j]}")
                s_single_worth_checking.append(s_peak_time[j])
                s_single_worth_checking_confidence.append(s_confidence[j])

    print(f"\nFind ({len(p_single_worth_checking)}/{len(p_single)}) single P picks and ({len(s_single_worth_checking)}/{len(s_single)}) single S picks that do not have a corresponding pair within 5 seconds.\n")

    return p_single, p_single_confidence, p_single_worth_checking, p_single_worth_checking_confidence, s_single, s_single_confidence, s_single_worth_checking, s_single_worth_checking_confidence, warning_num, p_log, s_log

def save_single_p_logs(results, station, start_time, end_time):
    p_single, p_single_confidence, p_single_worth_checking, p_single_worth_checking_confidence, s_single, s_single_confidence, s_single_worth_checking, s_single_worth_checking_confidence, warning_num, p_log, s_log = results
    df = pd.read_csv(StringIO("\n".join(p_log)))

    folder_save = "catalog/"
    file_save = f"{folder_save}p_single_{station}_{datetime.strptime(start_time, '%Y-%m-%d').strftime('%Y%m%d')}_{datetime.strptime(end_time, '%Y-%m-%d').strftime('%Y%m%d')}.csv"
    if not os.path.exists(folder_save):
        os.makedirs(folder_save)
    df.to_csv(file_save, index=False)

def load_single_P_catalog(station, start_time, end_time):
    stations = [
        ("BG", station, "*", "*"),   # (network, station, location, channel)
    ]

    folder_load = "catalog/"
    file = f'p_single_{station}_{datetime.strptime(start_time, "%Y-%m-%d").strftime("%Y%m%d")}_{datetime.strptime(end_time, "%Y-%m-%d").strftime("%Y%m%d")}.csv'

    df = pd.read_csv(f"{folder_load}{file}")
    p_start_lst = df['p_start_time'].tolist()
    p_pick_lst = df['p_peak_time'].tolist()
    p_start_lst = [UTCDateTime(t) for t in p_start_lst]
    p_pick_lst = [UTCDateTime(t) for t in p_pick_lst]

    
    return p_start_lst, p_pick_lst, stations

def event_magnitude_check(p_start, window_length=5):
    client_catalog = Client("USGS")
    
    catalog = client_catalog.get_events(
        starttime  = p_start - window_length,
        endtime    = p_start + window_length,
        maxmagnitude = 0.5,
        minlatitude  = 38.7,
        maxlatitude  = 38.9,
        minlongitude = -123,
        maxlongitude = -122.6,
    )
    
    print(catalog)

def plot_waveforms_with_picks(p_start_lst, p_pick_lst, stations, window_length=5):
    client = Client("NCEDC")

    for i, (p_start, p_pick) in enumerate(zip(p_start_lst, p_pick_lst)):
        print(f"Processing pick {i+1}/{len(p_pick_lst)}: P start at {p_start}, P peak at {p_pick}...")
        p_end = p_start + window_length

        marker_times = [
            (p_pick, "P", "red"),
        ]

        # --- Fetch waveforms ---
        st = None
        for net, sta, loc, cha in stations:
            try:
                print(f"Fetching {net}.{sta} from {p_start} to {p_end}...")
                fetched = client.get_waveforms(net, sta, loc, cha, p_start, p_end)
                st = fetched if st is None else st + fetched
            except Exception as e:
                print(f"Failed to fetch {net}.{sta}: {e}")

        if st is None:
            print("No data fetched.")
        else:
            try:
                event_magnitude_check(p_start, 10)
            except:
                print("### No events found in magnitude catalog check. ###")

            st.merge(fill_value="interpolate")  # merge gaps if any
            st.detrend("demean")
            st.sort()
            # print(st)

            fig = st.plot(handle=True)

            for ax in fig.axes:
                for t, label, color in marker_times:
                    ax.axvline(x=t.matplotlib_date, color=color, linestyle="--", linewidth=1.5, label=label)
                    ax.legend(fontsize=8)

            folder_save = f"img/{sta}/"
            file_save = f"{folder_save}{sta}_{p_start.strftime('%Y%m%dT%H%M%S')}_{window_length}s.png"
            if not os.path.exists(folder_save):
                os.makedirs(folder_save)
            plt.savefig(file_save, dpi=100)
