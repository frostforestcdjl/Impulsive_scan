# --- basic info ---
BASE_URL = "https://dasway.ess.washington.edu/quakescope/service/picks/"
STATION_INFO = "gaysers_nw.csv"

# --- scan parameters ---
start_time = '2024-02-01'
end_time = '2024-02-28'
station = 'ACR'

confidence_threshold = 0.9

# --- waveform parameters ---
window_length = 5  # seconds from event start time to the end of the window for waveform retrieval
