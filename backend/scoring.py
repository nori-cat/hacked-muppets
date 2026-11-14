from classifier import scale

# Score band for each class (0 = worst, 100 = best).
# The band guarantees the score and the label never contradict each other.
BANDS = {
    "clear_water": (80, 97),
    "sediment": (35, 60),
    "algae": (20, 45),
    "pollution": (5, 30),
}


def calculate_score(classification, confidence, f):
    low, high = BANDS.get(classification, (40, 60))

    if classification == "clear_water":
        # Bluer water = clearer = closer to the top of the band.
        score = low + (high - low) * scale(f["blue_frac"], 0.10, 0.80)

        # Nothing clearly matched: don't hand out a great score.
        if confidence <= 50:
            score = min(score, 60)
    else:
        # More coverage of the problem = closer to the bottom of the band.
        if classification == "sediment":
            severity = scale(f["brown_frac"], 0.30, 0.70)
        elif classification == "algae":
            severity = scale(f["green_frac"], 0.45, 0.75)
        else:  # pollution
            severity = max(
                scale(f["specks"], 10, 35),
                scale(f["hue_entropy"], 3.0, 4.0),
            )
        score = high - (high - low) * severity

    return int(round(score))