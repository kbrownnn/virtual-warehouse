from matplotlib.cm import viridis


def item_locations(locations, items, balance):
    item_to_loc = {}
    for date, bl in balance.items():
        item_to_loc[date] = {}
        for loc_id, inv in bl.items():
            if not inv.item_id in item_to_loc[date]:
                item_to_loc[date][inv.item_id] = []
            item_to_loc[date][inv.item_id].append(loc_id)

    return item_to_loc


def calculate_frquencies(locations, items, balance, orders):
    item_locs = item_locations(locations, items, balance)

    date = list(item_locs.keys())[-1]

    for k, o in orders.items():
        for loc in item_locs[date][o.item_id]:
            locations[loc].freq += o.total_qty


def get_heatmap_color(val):
    """Convert 0-1 value into #RRGGBB color."""
    v = viridis(val, bytes=True)
    return f"#{v[0]:02X}{v[1]:02X}{v[2]:02X}"
