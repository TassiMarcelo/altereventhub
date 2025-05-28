


def calculate_average_rating(ratings):
    
    valid_ratings = [r.rating for r in ratings if r.is_current and not r.bl_baja]
    if valid_ratings:
        return sum(valid_ratings) / len(valid_ratings)
    return 0