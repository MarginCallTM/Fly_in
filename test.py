from map_parser import MapParser, MapParseError

p = MapParser()

# Test 1 — devrait planter sur la première zone avec "zone parser not ready"
try:
    p.parse("maps/easy/01_linear_path.txt")
except MapParseError as e:
    print(f"Got expected error: {e}")
    # Attendu : "Line 4: zone parser not ready"
