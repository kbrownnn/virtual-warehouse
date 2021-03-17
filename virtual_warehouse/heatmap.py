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


# Bytes representing values of viridis colors for 0 to 255
VIRIDIS_COLORS = b'D\x01TD\x02UD\x03WE\x05XE\x06ZE\x08[F\t\\F\x0b^F\x0c_F\x0eaG\x0fbG\x11cG\x12eG\x14fG\x15gG\x16iG\x18jH\x19kH\x1alH\x1cnH\x1doH\x1epH qH!rH"sH#tG%uG&vG\'wG(xG*yG+zG,{F-|F/|F0}F1~E2\x7fE4\x7fE5\x80E6\x81D7\x81D9\x82C:\x83C;\x83C<\x84B=\x84B>\x85B@\x85AA\x86AB\x86@C\x87@D\x87?E\x87?G\x88>H\x88>I\x89=J\x89=K\x89=L\x89<M\x8a<N\x8a;P\x8a;Q\x8a:R\x8b:S\x8b9T\x8b9U\x8b8V\x8b8W\x8c7X\x8c7Y\x8c6Z\x8c6[\x8c5\\\x8c5]\x8c4^\x8d4_\x8d3`\x8d3a\x8d2b\x8d2c\x8d1d\x8d1e\x8d1f\x8d0g\x8d0h\x8d/i\x8d/j\x8d.k\x8e.l\x8e.m\x8e-n\x8e-o\x8e,p\x8e,q\x8e,r\x8e+s\x8e+t\x8e*u\x8e*v\x8e*w\x8e)x\x8e)y\x8e(z\x8e(z\x8e({\x8e\'|\x8e\'}\x8e\'~\x8e&\x7f\x8e&\x80\x8e&\x81\x8e%\x82\x8e%\x83\x8d$\x84\x8d$\x85\x8d$\x86\x8d#\x87\x8d#\x88\x8d#\x89\x8d"\x89\x8d"\x8a\x8d"\x8b\x8d!\x8c\x8d!\x8d\x8c!\x8e\x8c \x8f\x8c \x90\x8c \x91\x8c\x1f\x92\x8c\x1f\x93\x8b\x1f\x94\x8b\x1f\x95\x8b\x1f\x96\x8b\x1e\x97\x8a\x1e\x98\x8a\x1e\x99\x8a\x1e\x99\x8a\x1e\x9a\x89\x1e\x9b\x89\x1e\x9c\x89\x1e\x9d\x88\x1e\x9e\x88\x1e\x9f\x88\x1e\xa0\x87\x1f\xa1\x87\x1f\xa2\x86\x1f\xa3\x86 \xa4\x85 \xa5\x85!\xa6\x85!\xa7\x84"\xa7\x84#\xa8\x83#\xa9\x82$\xaa\x82%\xab\x81&\xac\x81\'\xad\x80(\xae\x7f)\xaf\x7f*\xb0~+\xb1},\xb1}.\xb2|/\xb3{0\xb4z2\xb5z3\xb6y5\xb7x6\xb8w8\xb9v9\xb9v;\xbau=\xbbt>\xbcs@\xbdrB\xbeqD\xbepE\xbfoG\xc0nI\xc1mK\xc2lM\xc2kO\xc3iQ\xc4hS\xc5gU\xc6fW\xc6eY\xc7d[\xc8b^\xc9a`\xc9`b\xca_d\xcb]g\xcc\\i\xcc[k\xcdYm\xceXp\xceVr\xcfUt\xd0Tw\xd0Ry\xd1Q|\xd2O~\xd2N\x81\xd3L\x83\xd3K\x86\xd4I\x88\xd5G\x8b\xd5F\x8d\xd6D\x90\xd6C\x92\xd7A\x95\xd7?\x97\xd8>\x9a\xd8<\x9d\xd9:\x9f\xd98\xa2\xda7\xa5\xda5\xa7\xdb3\xaa\xdb2\xad\xdc0\xaf\xdc.\xb2\xdd,\xb5\xdd+\xb7\xdd)\xba\xde\'\xbd\xde&\xbf\xdf$\xc2\xdf"\xc5\xdf!\xc7\xe0\x1f\xca\xe0\x1e\xcd\xe0\x1d\xcf\xe1\x1c\xd2\xe1\x1b\xd4\xe1\x1a\xd7\xe2\x19\xda\xe2\x18\xdc\xe2\x18\xdf\xe3\x18\xe1\xe3\x18\xe4\xe3\x18\xe7\xe4\x19\xe9\xe4\x19\xec\xe4\x1a\xee\xe5\x1b\xf1\xe5\x1c\xf3\xe5\x1e\xf6\xe6\x1f\xf8\xe6!\xfa\xe6"\xfd\xe7$'


def get_heatmap_color(val):
    """Convert 0-1 value into #RRGGBB color."""
    val = int(val * 255)
    v = [VIRIDIS_COLORS[3 * val + i] for i in range(3)]
    return f"#{v[0]:02X}{v[1]:02X}{v[2]:02X}"
