from machine import Pin, ADC
import time
import json

# --- PIN DEFINITIONS ---
diode_adc   = ADC(Pin(26))      # Physical Pin 31: Temperature Diode
led_adc     = ADC(Pin(27))      # Physical Pin 32: Turbidity Detector LED (red LED + 100k parallel)
ppm_adc     = ADC(Pin(28))      # Physical Pin 34: PPM Water Probe Read
ppm_pwr     = Pin(14, Pin.OUT)  # Physical Pin 19: PPM Voltage Control
onboard_led = Pin(25, Pin.OUT)

# --- CALIBRATION CONSTANTS ---
# 1. Temperature Diode
COLD_TEMP_C    = 4.0
RAW_COLD       = 11645
WARM_TEMP_C    = 38.0
RAW_WARM       = 10650

# 2. Turbidity (reading goes UP when turbid)
#    CLEAR is re-measured at boot (see CALIBRATE_TURBIDITY_ON_BOOT), so tap-water
#    drift, ambient light and LED aging don't pin the result at 100%.
#    SPAN is how many raw counts above clear equals 100% turbid.
#    PLACEHOLDER: the old 255 came from the old read method (~975 clear).
#    With the new read (~5000 clear) set this to (murky raw - clear raw),
#    using the "raw.turb" values from the printout.
CALIBRATE_TURBIDITY_ON_BOOT = True
RAW_TURB_CLEAR = 5000.0         # fallback if boot calibration is disabled
TURB_SPAN      = 1300.0         # placeholder, measure and replace

# 3. Differential PPM
DIFF_PPM_AIR   = 5000     # Below this = empty/dry tube (0 PPM)
DIFF_PPM_TAP   = 54000    # Clean tap water baseline (~150 PPM)
DIFF_PPM_SALT  = 61000    # Contaminated / salty water (~650 PPM)


def read_stable(adc_pin, samples=50):
    # Throw away the first reads: the RP2040 ADC mux carries charge over
    # from the previously sampled channel.
    for _ in range(3):
        adc_pin.read_u16()
    total = 0
    for _ in range(samples):
        total += adc_pin.read_u16()
        time.sleep_ms(2)
    return total / samples


def read_turbidity(samples=200):
    # The LED + 100k is a high-impedance source, so (a) discard settling reads
    # after the channel switch and (b) spread samples over ~100 ms so room-light
    # flicker (60 Hz) averages out instead of aliasing.
    # Raw values from this method are NOT comparable to the old logs
    # (clear ~5000 instead of ~975), so TURB_SPAN must be set from new data.
    for _ in range(5):
        led_adc.read_u16()
    total = 0
    for _ in range(samples):
        total += led_adc.read_u16()
        time.sleep_us(500)
    return total / samples


def read_ppm_diff(pulse_us=30, samples=25):
    total = 0
    for _ in range(samples):
        ppm_pwr.value(0)
        time.sleep_ms(8)
        residual = ppm_adc.read_u16()

        ppm_pwr.value(1)
        time.sleep_us(pulse_us)
        active = ppm_adc.read_u16()
        ppm_pwr.value(0)

        total += max(0, active - residual)
    return total // samples


def calc_temp_c(raw):
    slope = (WARM_TEMP_C - COLD_TEMP_C) / (RAW_WARM - RAW_COLD)
    return COLD_TEMP_C + (raw - RAW_COLD) * slope


def calc_ppm(diff):
    if diff < DIFF_PPM_AIR:
        return 0
    if diff <= DIFF_PPM_TAP:
        ppm = 50 + (diff - DIFF_PPM_AIR) * (100 / (DIFF_PPM_TAP - DIFF_PPM_AIR))
    else:
        ppm = 150 + (diff - DIFF_PPM_TAP) * (500 / (DIFF_PPM_SALT - DIFF_PPM_TAP))
    return max(0, int(ppm))


def calc_turbidity_pct(raw):
    # 0% at the clear baseline, 100% at baseline + TURB_SPAN
    turb = (raw - RAW_TURB_CLEAR) / TURB_SPAN * 100.0
    return round(max(0.0, min(100.0, turb)), 1)


def get_water_status(ppm, turb):
    if ppm == 0:
        return "NO WATER / DRY"
    if turb > 50.0 or ppm > 400:
        return "CONTAMINATED"
    if turb > 20.0 or ppm > 250:
        return "MODERATE / CHECK"
    return "CLEAN / SAFE"


def calibrate_turbidity_baseline():
    """Wait for water in the tube, let it settle, then take the current
    turbidity reading as 'clear'. Start the unit in CLEAN water."""
    global RAW_TURB_CLEAR
    while read_ppm_diff() < DIFF_PPM_AIR:
        onboard_led.toggle()
        print(json.dumps({"event": "waiting_for_water"}))
        time.sleep(1)
    time.sleep(2)  # let bubbles / ripples settle
    readings = sorted(read_turbidity() for _ in range(7))
    RAW_TURB_CLEAR = readings[3]  # median
    print(json.dumps({"event": "turbidity_baseline", "raw_clear": round(RAW_TURB_CLEAR, 1)}))


if CALIBRATE_TURBIDITY_ON_BOOT:
    calibrate_turbidity_baseline()

while True:
    onboard_led.toggle()
    d_raw  = read_stable(diode_adc)
    l_raw  = read_turbidity()
    p_diff = read_ppm_diff(pulse_us=30)

    temp_c = round(calc_temp_c(d_raw), 1)
    ppm    = calc_ppm(p_diff)
    turb   = calc_turbidity_pct(l_raw)
    status = get_water_status(ppm, turb)

    payload = {
        "status": status,
        "temp_c": temp_c,
        "ppm": ppm,
        "turbidity_pct": turb,
        # raw values so you can recalibrate from the printed log
        "raw": {
            "temp": round(d_raw),
            "turb": round(l_raw, 1),
            "ppm_diff": p_diff
        }
    }
    print(json.dumps(payload))
    time.sleep(0.3)