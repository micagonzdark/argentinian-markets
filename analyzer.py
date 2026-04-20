import numpy as np
from scipy.signal import savgol_filter

def calculate_snr(series, window_length=31, polyorder=3):
    """
    Extracts the underlying 'Signal' using a Savitzky-Golay low-pass filter,
    calculates the 'Noise' (Original Price - Signal), and returns the Signal-to-Noise Ratio (SNR).
    """
    if len(series) < window_length:
        return np.nan
    
    # Convert to numpy array safely
    series_arr = np.array(series)
    
    # 1. Extract Signal
    signal = savgol_filter(series_arr, window_length=window_length, polyorder=polyorder)
    
    # 2. Calculate Noise
    noise = series_arr - signal
    
    # 3. Calculate Standard Deviations
    std_signal = np.std(signal)
    std_noise = np.std(noise)
    
    # 4. Return SNR Ratio
    if std_noise == 0:
        return np.inf
    return std_signal / std_noise
