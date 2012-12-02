#Gratefully Borrowed from MB Picard!
def sanitize_date(datestr):
    """Sanitize date format.

e.g.: "YYYY-00-00" -> "YYYY"
"YYYY- - " -> "YYYY"
...
"""
    date = []
    for num in datestr.split("-"):
        try:
            num = int(num.strip())
        except ValueError:
            break
        if num:
            date.append(num)
    return ("", "%04d", "%04d-%02d", "%04d-%02d-%02d")[len(date)] % tuple(date)

