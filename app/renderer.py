"""
Postcard rendering module.
Refactored from create_map_poster.py for web app use.
Creates landscape postcards with map on left, message on right.
"""
import io
import os
import time
import textwrap
from pathlib import Path

import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend for thread safety

import osmnx as ox
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
import matplotlib.colors as mcolors
import numpy as np
from geopy.geocoders import Nominatim

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
FONTS_DIR = PROJECT_ROOT / "fonts"


def load_fonts():
    """
    Load Roboto fonts from the fonts directory.
    Returns dict with FontProperties for different weights.
    """
    fonts = {
        'bold': FONTS_DIR / 'Roboto-Bold.ttf',
        'regular': FONTS_DIR / 'Roboto-Regular.ttf',
        'light': FONTS_DIR / 'Roboto-Light.ttf'
    }

    # Verify fonts exist
    for weight, path in fonts.items():
        if not path.exists():
            return None

    return {k: str(v) for k, v in fonts.items()}


FONTS = load_fonts()


def get_coordinates(city: str, country: str) -> tuple[float, float]:
    """
    Fetches coordinates for a given city and country using geopy.
    """
    geolocator = Nominatim(user_agent="maptoposter_webapp")
    time.sleep(1)  # Respect rate limits

    location = geolocator.geocode(f"{city}, {country}")

    if location:
        return (location.latitude, location.longitude)
    else:
        raise ValueError(f"Could not find coordinates for {city}, {country}")


def get_edge_colors_by_type(G, theme: dict) -> list[str]:
    """
    Assigns colors to edges based on road type hierarchy.
    """
    edge_colors = []

    for u, v, data in G.edges(data=True):
        highway = data.get('highway', 'unclassified')

        if isinstance(highway, list):
            highway = highway[0] if highway else 'unclassified'

        if highway in ['motorway', 'motorway_link']:
            color = theme['road_motorway']
        elif highway in ['trunk', 'trunk_link', 'primary', 'primary_link']:
            color = theme['road_primary']
        elif highway in ['secondary', 'secondary_link']:
            color = theme['road_secondary']
        elif highway in ['tertiary', 'tertiary_link']:
            color = theme['road_tertiary']
        elif highway in ['residential', 'living_street', 'unclassified']:
            color = theme['road_residential']
        else:
            color = theme['road_default']

        edge_colors.append(color)

    return edge_colors


def get_edge_widths_by_type(G) -> list[float]:
    """
    Assigns line widths to edges based on road type.
    """
    edge_widths = []

    for u, v, data in G.edges(data=True):
        highway = data.get('highway', 'unclassified')

        if isinstance(highway, list):
            highway = highway[0] if highway else 'unclassified'

        if highway in ['motorway', 'motorway_link']:
            width = 1.2
        elif highway in ['trunk', 'trunk_link', 'primary', 'primary_link']:
            width = 1.0
        elif highway in ['secondary', 'secondary_link']:
            width = 0.8
        elif highway in ['tertiary', 'tertiary_link']:
            width = 0.6
        else:
            width = 0.4

        edge_widths.append(width)

    return edge_widths


def create_gradient_fade(ax, color: str, location: str = 'bottom', zorder: int = 10):
    """
    Creates a fade effect at the top or bottom of the map.
    """
    vals = np.linspace(0, 1, 256).reshape(-1, 1)
    gradient = np.hstack((vals, vals))

    rgb = mcolors.to_rgb(color)
    my_colors = np.zeros((256, 4))
    my_colors[:, 0] = rgb[0]
    my_colors[:, 1] = rgb[1]
    my_colors[:, 2] = rgb[2]

    if location == 'bottom':
        my_colors[:, 3] = np.linspace(1, 0, 256)
        extent_y_start = 0
        extent_y_end = 0.25
    else:
        my_colors[:, 3] = np.linspace(0, 1, 256)
        extent_y_start = 0.75
        extent_y_end = 1.0

    custom_cmap = mcolors.ListedColormap(my_colors)

    xlim = ax.get_xlim()
    ylim = ax.get_ylim()
    y_range = ylim[1] - ylim[0]

    y_bottom = ylim[0] + y_range * extent_y_start
    y_top = ylim[0] + y_range * extent_y_end

    ax.imshow(gradient, extent=[xlim[0], xlim[1], y_bottom, y_top],
              aspect='auto', cmap=custom_cmap, zorder=zorder, origin='lower')


def render_map_side(ax, city: str, country: str, point: tuple, dist: int, theme: dict, fast: bool = False):
    """
    Render the map on the left side of the postcard.
    fast=True skips water/parks and uses simpler network for speed.
    """
    ax.set_facecolor(theme['bg'])

    # Fetch map data - use 'drive' network in fast mode (fewer roads, faster)
    network_type = 'drive' if fast else 'all'
    G = ox.graph_from_point(point, dist=dist, dist_type='bbox', network_type=network_type)

    water = None
    parks = None

    # Skip water/parks in fast mode
    if not fast:
        try:
            water = ox.features_from_point(point, tags={'natural': 'water', 'waterway': 'riverbank'}, dist=dist)
        except:
            water = None

        try:
            parks = ox.features_from_point(point, tags={'leisure': 'park', 'landuse': 'grass'}, dist=dist)
        except:
            parks = None

    # Plot layers
    if water is not None and not water.empty:
        water.plot(ax=ax, facecolor=theme['water'], edgecolor='none', zorder=1)
    if parks is not None and not parks.empty:
        parks.plot(ax=ax, facecolor=theme['parks'], edgecolor='none', zorder=2)

    # Roads
    edge_colors = get_edge_colors_by_type(G, theme)
    edge_widths = get_edge_widths_by_type(G)

    ox.plot_graph(
        G, ax=ax, bgcolor=theme['bg'],
        node_size=0,
        edge_color=edge_colors,
        edge_linewidth=edge_widths,
        show=False, close=False
    )

    # Gradients
    create_gradient_fade(ax, theme['gradient_color'], location='bottom', zorder=10)
    create_gradient_fade(ax, theme['gradient_color'], location='top', zorder=10)

    # Typography
    if FONTS:
        font_main = FontProperties(fname=FONTS['bold'], size=36)
        font_sub = FontProperties(fname=FONTS['light'], size=16)
        font_coords = FontProperties(fname=FONTS['regular'], size=10)
    else:
        font_main = FontProperties(family='monospace', weight='bold', size=36)
        font_sub = FontProperties(family='monospace', weight='normal', size=16)
        font_coords = FontProperties(family='monospace', size=10)

    spaced_city = "  ".join(list(city.upper()))

    # Bottom text on map
    ax.text(0.5, 0.12, spaced_city, transform=ax.transAxes,
            color=theme['text'], ha='center', fontproperties=font_main, zorder=11)

    ax.text(0.5, 0.08, country.upper(), transform=ax.transAxes,
            color=theme['text'], ha='center', fontproperties=font_sub, zorder=11)

    lat, lon = point
    coords = f"{lat:.4f}\u00b0 N / {lon:.4f}\u00b0 E" if lat >= 0 else f"{abs(lat):.4f}\u00b0 S / {lon:.4f}\u00b0 E"
    if lon < 0:
        coords = coords.replace("E", "W")

    ax.text(0.5, 0.05, coords, transform=ax.transAxes,
            color=theme['text'], alpha=0.7, ha='center', fontproperties=font_coords, zorder=11)

    # Decorative line
    ax.plot([0.3, 0.7], [0.10, 0.10], transform=ax.transAxes,
            color=theme['text'], linewidth=1, zorder=11)

    ax.axis('off')


def render_message_side(ax, message: str, theme: dict):
    """
    Render the message on the right side of the postcard.
    """
    ax.set_facecolor(theme['bg'])
    ax.axis('off')

    if not message.strip():
        return

    if FONTS:
        font_message = FontProperties(fname=FONTS['regular'], size=18)
    else:
        font_message = FontProperties(family='serif', size=18)

    # Word wrap the message
    wrapped_lines = []
    for paragraph in message.split('\n'):
        if paragraph.strip():
            wrapped = textwrap.wrap(paragraph, width=35)
            wrapped_lines.extend(wrapped)
        else:
            wrapped_lines.append('')

    wrapped_message = '\n'.join(wrapped_lines)

    # Render message text
    ax.text(0.1, 0.85, wrapped_message, transform=ax.transAxes,
            fontproperties=font_message, color=theme['text'],
            verticalalignment='top', horizontalalignment='left',
            linespacing=1.5)

    # Add postcard-style stamp area (decorative)
    stamp_rect = plt.Rectangle((0.7, 0.75), 0.2, 0.15, transform=ax.transAxes,
                                 fill=False, edgecolor=theme['text'],
                                 linewidth=1, linestyle='--', alpha=0.3)
    ax.add_patch(stamp_rect)
    ax.text(0.8, 0.825, "STAMP", transform=ax.transAxes,
            fontproperties=FontProperties(family='monospace', size=8),
            color=theme['text'], alpha=0.3, ha='center', va='center')

    # Add decorative lines for "address" area
    for y in [0.4, 0.32, 0.24, 0.16]:
        ax.plot([0.1, 0.9], [y, y], transform=ax.transAxes,
                color=theme['text'], linewidth=0.5, alpha=0.3)

    # Attribution
    if FONTS:
        font_attr = FontProperties(fname=FONTS['light'], size=6)
    else:
        font_attr = FontProperties(family='monospace', size=6)

    ax.text(0.9, 0.03, "\u00a9 OpenStreetMap contributors", transform=ax.transAxes,
            color=theme['text'], alpha=0.5, ha='right', va='bottom',
            fontproperties=font_attr)


def create_postcard(
    city: str,
    country: str,
    point: tuple[float, float],
    dist: int,
    theme: dict,
    message: str,
    fast: bool = False
) -> bytes:
    """
    Create a landscape postcard with map on left and message on right.

    Args:
        fast: If True, uses optimizations for speed (~10s vs ~60s):
              - Skips water/parks layers
              - Uses 'drive' network (fewer roads)
              - Lower DPI (150 vs 300)

    Returns PNG image as bytes.
    """
    # Landscape figure: 16x10 inches (standard postcard ratio)
    fig, (ax_map, ax_text) = plt.subplots(
        1, 2,
        figsize=(16, 10),
        gridspec_kw={'width_ratios': [1, 1]},
        facecolor=theme['bg']
    )

    # Remove spacing between subplots
    plt.subplots_adjust(wspace=0.02, left=0, right=1, top=1, bottom=0)

    # Render both sides
    render_map_side(ax_map, city, country, point, dist, theme, fast=fast)
    render_message_side(ax_text, message, theme)

    # Add a subtle divider line between the two sides
    line = plt.Line2D([0.5, 0.5], [0.05, 0.95], transform=fig.transFigure,
                       color=theme['text'], linewidth=0.5, alpha=0.3)
    fig.add_artist(line)

    # Save to bytes - lower DPI in fast mode
    dpi = 150 if fast else 300
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=dpi, facecolor=theme['bg'],
                bbox_inches='tight', pad_inches=0)
    plt.close(fig)

    buf.seek(0)
    return buf.getvalue()
