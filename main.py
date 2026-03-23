import config
from utils import search_target, save_single_p_logs, load_single_P_catalog, plot_waveforms_with_picks

"""
Impulsive P-wave Detection and Analysis Pipeline.

If you have any questions or need further assistance, please feel free to contact me with the following information:
- Name: Chris Lin
- Email: chrisdjlin@gmail.com

"""

base_url = config.BASE_URL
station = config.station
start_time = config.start_time
end_time = config.end_time
confidence_threshold = config.confidence_threshold
window_length = config.window_length


if __name__ == "__main__":
    print(f"Querying picks: station=[{station}], from [{start_time}] to [{end_time}], Confidence threshold=[{confidence_threshold}]")
    results = search_target(base_url, station, start_time, end_time, confidence_threshold)
    save_single_p_logs(results, station, start_time, end_time)
    p_start_lst, p_pick_lst, stations = load_single_P_catalog(station, start_time, end_time)
    plot_waveforms_with_picks(p_start_lst, p_pick_lst, stations, window_length)