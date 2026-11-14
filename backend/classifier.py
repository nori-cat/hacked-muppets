def classify_water(red, green, blue):

    confidence = 50

    if green > red + 15:
        confidence = min(
            100,
            50 + (green - red)
        )
        classification = "algae"

    elif red > blue + 15:
        confidence = min(
            100,
            50 + (red - blue)
        )
        classification = "sediment"

    else:
        confidence = 70
        classification = "clear_water"

    return classification, confidence