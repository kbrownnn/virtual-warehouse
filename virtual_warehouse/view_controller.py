from PySide2.QtCore import Property, QObject, Qt, QThread, QUrl, Signal, Slot

import virtual_warehouse.parser.excel_parser as parser
from virtual_warehouse.heatmap import calculate_frquencies
from virtual_warehouse.location_models import (
    MultiLocation,
    SingleLocation,
    UniversalLocationListModel,
)
from virtual_warehouse.location_utils import cluster_locations
from virtual_warehouse.parser.data_model import Item, Location, Order
from virtual_warehouse.tab_controller import (
    HoverListModel,
    TabItem,
    TabLocation,
    TabOrder,
    UniversalListModel,
)


class DataLoaderThread(QThread):
    """Thread which loads data from file."""

    dataReady = Signal(object)

    def __init__(self, file_path):
        super(DataLoaderThread, self).__init__()
        self.file_path = file_path

    def run(self):
        """Load data from file path and emit data through signal."""
        # TODO: Split on loading of individual elements, measure speed?
        locations, items, balance, orders = parser.parse_document(
            QUrl(self.file_path).toLocalFile()
        )
        # TODO: Calculate after initial draw
        calculate_frquencies(locations, balance, orders)
        self.data = (locations, items, balance, orders)
        self.dataReady.emit(self.data)


class Map(QObject):
    """Object holding basic informations about the map."""

    def __init__(self, locations=None):
        QObject.__init__(self)
        if locations:
            self.set_data(locations)
        else:
            self._min_x = 0
            self._max_x = 0
            self._min_y = 0
            self._max_y = 0
            self._min_z = 0
            self._max_z = 0

    def set_data(self, locations):
        self._min_x = min(l.has_x for l in locations.values())
        self._max_x = max(l.has_x + l.has_width for l in locations.values())

        self._min_y = min(l.has_y for l in locations.values())
        self._max_y = max(l.has_y + l.has_length for l in locations.values())

        self._min_z = min(l.has_z for l in locations.values())
        self._max_z = max(l.has_z + l.has_height for l in locations.values())

    @Property(float, constant=True)
    def min_x(self):
        return self._min_x

    @Property(float, constant=True)
    def max_x(self):
        return self._max_x

    @Property(float, constant=True)
    def min_y(self):
        return self._min_y

    @Property(float, constant=True)
    def max_y(self):
        return self._max_y

    @Property(float, constant=True)
    def min_z(self):
        return self._min_z

    @Property(float, constant=True)
    def max_z(self):
        return self._max_z


class ViewController(QObject):
    """Main controller which communicates with QML GUI."""

    def __init__(self, parent=None):
        super(ViewController, self).__init__(parent)

        self._is2D = True
        self._is_heatmap = False

        self._model3D = UniversalLocationListModel(on_change=self.modelChanged.emit)
        self._model2D = UniversalLocationListModel(on_change=self.modelChanged.emit)
        self._map = Map()

        self._sidebar_model = HoverListModel(TabLocation)
        self._location_model = UniversalListModel(TabLocation)
        self._item_model = UniversalListModel(TabItem)
        self._order_model = UniversalListModel(TabOrder)

        self.selected_idxs = set()
        self.reset_selection()
        self.locations = {}

        self._progress_value = 1

        # DEBUG:
        self.load(
            "file:///home/breta/Documents/github/virtual-warehouse/data/warehouse_no_1_v2.xlsx"
        )

    modelChanged = Signal()
    sidebarChanged = Signal()
    drawModeChanged = Signal()
    itemSelected = Signal()
    progressChanged = Signal()

    @Property(QObject, constant=False, notify=modelChanged)
    def map(self):
        return self._map

    @Property(QObject, constant=False, notify=modelChanged)
    def model(self):
        return self._model2D if self._is2D else self._model3D

    @Property(QObject, constant=False, notify=modelChanged)
    def model2D(self):
        return self._model2D

    @Property(QObject, constant=False, notify=modelChanged)
    def model3D(self):
        return self._model3D

    @Property(QObject, constant=False, notify=modelChanged)
    def location_model(self):
        return self._location_model

    @Property(QObject, constant=False, notify=sidebarChanged)
    def sidebar_model(self):
        return self._sidebar_model

    @Property(QObject, constant=False, notify=modelChanged)
    def item_model(self):
        return self._item_model

    @Property(QObject, constant=False, notify=modelChanged)
    def order_model(self):
        return self._order_model

    @Property(bool, constant=False, notify=drawModeChanged)
    def is_heatmap(self):
        return self._is_heatmap

    @Property(float, constant=False, notify=progressChanged)
    def progress_value(self):
        return self._progress_value

    @progress_value.setter
    def set_progress_value(self, val):
        self._progress_value = val
        self.progressChanged.emit()

    @Slot(result=bool)
    def is2D(self):
        return self._is2D

    @Slot()
    def switch_heatmap(self):
        self._is_heatmap = not self._is_heatmap
        self.drawModeChanged.emit()

    @Slot()
    def switch_view(self):
        """Switch 2D - 3D model and update selection."""
        self._is2D = not self._is2D
        self.reset_selection()
        for name in self._location_model._checked:
            idx = self.model._name_to_idx[name]
            self.selected_idxs.add(idx)
        self.itemSelected.emit()

    @Slot(str, bool)
    def checked_location(self, selected, val):
        """Location checked in tab list."""
        idx = self.model._name_to_idx[selected]
        if val:
            self.selected_idxs.add(idx)
        else:
            self.selected_idxs.discard(idx)
        self.itemSelected.emit()

    @Slot(int, bool)
    def select_item(self, idx, control=False):
        """Location selected from map (CTRL adds location)."""
        if not control:
            self.reset_selection()
        if idx >= 0:
            self.selected_idxs.add(idx)
            names = self.model._get_idx(idx).names
            self._location_model.set_checked(names, control)
            self._sidebar_model.set_selected(names)
        else:
            self._location_model.set_checked([])
            self._sidebar_model.set_selected([])
        self.itemSelected.emit()

    # Connecting sidebar tabs
    # TODO: run in separate thread
    def _connect_tabs(self, src_tab_model, dst_tab_model, connector):
        if src_tab_model._checked:
            objs = [src_tab_model._objects[k]._i for k in src_tab_model._checked]
            res = connector(objs)
            dst_tab_model.set_checked([i[0].name for i in res])
        else:
            dst_tab_model.set_checked([])

    @Slot()
    def checked_locations_to_items(self):
        self._connect_tabs(
            self._location_model, self._item_model, Item.get_by_locations
        )

    @Slot()
    def checked_orders_to_items(self):
        self._connect_tabs(self._order_model, self._item_model, Item.get_by_orders)

    @Slot()
    def checked_items_to_orders(self):
        self._connect_tabs(self._item_model, self._order_model, Order.get_by_items)

    @Slot()
    def checked_locations_to_orders(self):
        self._connect_tabs(
            self._location_model, self._order_model, Order.get_by_locations
        )

    @Slot()
    def checked_orders_to_locations(self):
        self._connect_tabs(
            self._order_model, self._location_model, Location.get_by_orders
        )

    @Slot()
    def checked_items_to_locations(self):
        self._connect_tabs(
            self._item_model, self._location_model, Location.get_by_items
        )

    @Slot(int)
    def hover_item(self, idx):
        if idx >= 0:
            names = self.model._get_idx(idx).names
            self._sidebar_model.set_hovered(names, True)
        else:
            self._sidebar_model.set_hovered([], False)
        self.sidebarChanged.emit()

    @Slot(result="QVariantList")
    def get_selected(self):
        return list(self.selected_idxs)

    @Slot()
    def reset_selection(self):
        self.selected_idxs.clear()

    @Slot(str)
    def load(self, file_path):
        self.progress_value = 0
        self.loader = DataLoaderThread(file_path)
        self.loader.dataReady.connect(self._load, Qt.QueuedConnection)
        self.loader.start()

    def _load(self, data):
        # TODO: Split loading into multiple steps, update progress bar
        #       updating progress bar requires extra thread
        locations, items, balance, orders = data

        self.reset_selection()
        self.locations = locations

        self._map.set_data(locations)
        self._location_model.set_data(locations)
        self._location_model.set_selected(
            # list(locations.keys())
            [k for k, v in locations.items() if v.has_ltype == "rack"]
        )

        self._sidebar_model.set_data(locations)

        self._item_model.set_data(items)
        self._item_model.set_selected(list(items.keys()))

        self._order_model.set_data(orders)
        self._order_model.set_selected(list(orders.keys()))

        self._model3D.set_data(
            {k: SingleLocation(v) for k, v in self.locations.items()}
        )

        clusters = cluster_locations(self.locations)
        multi_loc = {}
        for k, v in clusters.items():
            multi_loc[k] = MultiLocation([self.locations[l] for l in v])
        self._model2D.set_data(multi_loc)

        self.modelChanged.emit()
        self.progress_value = 1
