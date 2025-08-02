import folium
import numpy as np
import math
from itertools import combinations
from folium.plugins import HeatMap, MousePosition, Fullscreen, MiniMap, MarkerCluster
import branca.colormap as cm
import random
from scipy.spatial import ConvexHull

# Path loss parameters
TX_POWER = 43
PATH_LOSS_AT_1M = 32.4
PATH_LOSS_EXPONENT = 3.5

def generate_tower_data(base_tower, num_towers=3):
    towers = [base_tower]
    for i in range(1, num_towers):
        towers.append({
            "name": f"Tower {chr(ord('A') + i)}",
            "lat": base_tower["lat"] + random.uniform(-0.005, 0.005),
            "lon": base_tower["lon"] + random.uniform(-0.005, 0.005),
            "rsrp": base_tower["rsrp"] + random.randint(-10, 5)
        })
    return towers

def calculate_tower_properties(towers):
    for tower in towers:
        path_loss = TX_POWER - tower["rsrp"]
        distance_m = 10 ** ((path_loss - PATH_LOSS_AT_1M) / (10 * PATH_LOSS_EXPONENT))
        tower["distance"] = distance_m
        tower["weight"] = 1 / abs(tower["rsrp"])
    return towers

def get_circle_intersections(c1, c2):
    R = 6371e3
    lat1, lon1, r1 = math.radians(c1['lat']), math.radians(c1['lon']), c1['distance']
    lat2, lon2, r2 = math.radians(c2['lat']), math.radians(c2['lon']), c2['distance']

    d = 2 * R * math.asin(math.sqrt(
        math.sin((lat2 - lat1) / 2)**2 +
        math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2)**2
    ))

    if d > r1 + r2 or d < abs(r1 - r2) or d == 0:
        return []

    a = (r1**2 - r2**2 + d**2) / (2 * d)
    h = math.sqrt(max(r1**2 - a**2, 0))
    lat_mid = lat1 + (a / d) * (lat2 - lat1)
    lon_mid = lon1 + (a / d) * (lon2 - lon1)

    bearing = math.atan2(
        math.sin(lon2 - lon1) * math.cos(lat2),
        math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(lon2 - lon1)
    )

    points = []
    for sign in [-1, 1]:
        bearing_i = bearing + sign * math.atan2(h, a)
        lat_i = math.asin(math.sin(lat_mid) * math.cos(r1 / R) +
                          math.cos(lat_mid) * math.sin(r1 / R) * math.cos(bearing_i))
        lon_i = lon_mid + math.atan2(
            math.sin(bearing_i) * math.sin(r1 / R) * math.cos(lat_mid),
            math.cos(r1 / R) - math.sin(lat_mid) * math.sin(lat_i)
        )
        points.append([math.degrees(lat_i), math.degrees(lon_i)])
    return points

def get_trilateration(towers):
    all_intersections = []
    for t1, t2 in combinations(towers, 2):
        intersections = get_circle_intersections(t1, t2)
        all_intersections.extend(intersections)

    if not all_intersections:
        return None, None

    centroid_lat = sum(p[0] for p in all_intersections) / len(all_intersections)
    centroid_lon = sum(p[1] for p in all_intersections) / len(all_intersections)
    return [centroid_lat, centroid_lon], all_intersections

def generate_map(lat, lon, rsrp):
    base_tower = {"name": "Tower A", "lat": lat, "lon": lon, "rsrp": rsrp}
    towers = generate_tower_data(base_tower)
    towers = calculate_tower_properties(towers)
    est_centroid, intersection_points = get_trilateration(towers)

    if not est_centroid:
        est_centroid = [np.mean([t['lat'] for t in towers]), np.mean([t['lon'] for t in towers])]

    m = folium.Map(location=est_centroid, zoom_start=15, tiles="OpenStreetMap")
    fg_heatmap = folium.FeatureGroup(name="Signal Heatmap", show=False).add_to(m)
    fg_coverage = folium.FeatureGroup(name="Tower Coverage").add_to(m)
    fg_estimation = folium.FeatureGroup(name="Trilateration").add_to(m)
    fg_markers = folium.FeatureGroup(name="Tower Markers").add_to(m)
    marker_cluster = MarkerCluster().add_to(fg_markers)

    min_rsrp, max_rsrp = min(t["rsrp"] for t in towers), max(t["rsrp"] for t in towers)
    colormap = cm.LinearColormap(colors=['red', 'orange', 'green'], vmin=min_rsrp, vmax=max_rsrp)
    colormap.caption = 'RSRP Signal Strength (dBm)'
    m.add_child(colormap)

    for tower in towers:
        folium.Circle(
            radius=tower["distance"],
            location=[tower["lat"], tower["lon"]],
            color=colormap(tower["rsrp"]),
            fill=True,
            fill_opacity=0.2,
            tooltip=f"{tower['name']}: {tower['rsrp']} dBm"
        ).add_to(fg_coverage)
        folium.Marker([tower["lat"], tower["lon"]],
                      icon=folium.Icon(color="blue", icon="signal", prefix="fa"),
                      tooltip=tower['name']).add_to(marker_cluster)

    if intersection_points:
        for point in intersection_points:
            folium.CircleMarker(location=point, radius=5, color='blue', fill=True).add_to(fg_estimation)
        if len(intersection_points) > 2:
            hull = ConvexHull(intersection_points)
            hull_points = [intersection_points[i] for i in hull.vertices]
            folium.Polygon(locations=hull_points, color='purple', fill=True, fill_opacity=0.2).add_to(fg_estimation)

    folium.Marker(est_centroid, icon=folium.Icon(color="purple", icon="crosshairs", prefix="fa"),
                  tooltip="Estimated Location").add_to(fg_estimation)

    MousePosition().add_to(m)
    Fullscreen().add_to(m)
    MiniMap(toggle_display=True).add_to(m)

    map_filename = "trilateration_tower_map.html"
    m.save(map_filename)
    return map_filename
