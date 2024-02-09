def check_list_of_hours(hours: list[int]):
    if len(hours) > 24:
        raise ValueError('List of hours is too long')
    if not all(0 <= x < 24 for x in hours):
        raise ValueError('List of hours must only contain integers between 0 and 23')
    if len(set(hours)) != len(hours):
        raise ValueError('List of hours must contain different integers')
