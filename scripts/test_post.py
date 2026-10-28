"""Run: python3 scripts/test_post.py"""
from post import parse

BODY = """### Distillery

Lagavulin

### Style

Single malt Scotch

### Age

_No response_

### ABV

43%

### Region

_No response_

### Sweet

2

### Fruity

1

### Floral

0

### Spicy

3

### Oak

3

### Peaty

5

### Rating

4 - very good

### Tasting notes

Bonfire on a beach.

### Photo

<img width="800" alt="glass" src="https://github.com/user-attachments/assets/abc-123" />

### Link

https://www.whiskybase.com/whiskies/whisky/1234
"""

entry = parse({"number": 7, "title": " Lagavulin 16 ", "created_at": "2026-10-28T20:00:00Z",
               "labels": [{"name": "whiskey"}], "body": BODY.replace("\n", "\r\n")})
assert entry["category"] == "whiskey"
assert entry["title"] == "Lagavulin 16"
assert entry["details"] == {"Distillery": "Lagavulin", "Style": "Single malt Scotch", "ABV": "43%"}
assert entry["profile"] == {"Sweet": 2, "Fruity": 1, "Floral": 0, "Spicy": 3, "Oak": 3, "Peaty": 5}
assert entry["rating"] == 4
assert entry["notes"] == "Bonfire on a beach."
assert entry["image"] == "https://github.com/user-attachments/assets/abc-123"
assert entry["link"] == "https://www.whiskybase.com/whiskies/whisky/1234"
assert entry["date"] == "2026-10-28"
print("ok")
