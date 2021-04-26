"""Data model using Owlready2 ontology."""
import datetime
from typing import List

import owlready2
from owlready2 import (
    ConstrainedDatatype,
    DataProperty,
    FunctionalProperty,
    ObjectProperty,
    Thing,
    default_world,
    destroy_entity,
    get_ontology,
    sync_reasoner,
)
from PySide2.QtCore import Property, QObject, Signal, Slot

from virtual_warehouse.data.utils import (
    convert_date,
    convert_dim,
    convert_type,
    convert_weight,
)

# We could use actual irl with already created ontology
BASE_IRI = "http://warehouse/onto.owl"
onto = get_ontology(BASE_IRI)


def destroy_all(cls):
    """Destroy all instances of given class.

    Args:
        cls (class): ontology class
    """
    for i in cls.instances():
        destroy_entity(i)


def save_ontology(file_path):
    """Save ontology in RDF/XML format.

    Args:
        file_path (str): file url should be processed with QUrl(file_path)
    """
    onto.save(file_path, format="rdfxml")


class OntoManager(QObject):
    """Class controlling ontology classes and reasoning."""

    classesChanged = Signal()
    javaChanged = Signal()

    def __init__(self):
        """Initialize OntoController."""
        QObject.__init__(self)
        self._classes = {}

    @Property(str, constant=False, notify=javaChanged)
    def java(self):
        """Get Java executable path for owlready reasoner."""
        return owlready2.JAVA_EXE

    @java.setter
    def set_java(self, val):
        """Set Java executable path for owlready reasoner."""
        owlready2.JAVA_EXE = val
        self.javaChanged.emit()

    @Slot(str)
    def delete_class(self, cls):
        """Destroy given ontology class.

        Args:
            cls (str): name of new class for destruction
        """
        if cls in self._classes:
            destroy_entity(self._classes.pop(cls)[0])
            self.classesChanged.emit()

    @Property("QVariantList", constant=False, notify=classesChanged)
    def classes(self):
        return [
            {"name": k, "class": v[1], "count": len(v[0].instances())}
            for k, v in self._classes.items()
        ]

    @Slot(str, str, str)
    def create_class(self, name, cls, conditions):
        """Construct new ontology class based on Location, Item or Order.

        Args:
            name (str): name of new class
            cls (str): string describing class, possible values: "Location", "Item", "Order"
            conditions (str): describing condition (later replace by more complex structure)
        """
        # TODO: Checks, errors, background thread + loading
        assert cls in ["Location", "Item", "Order"], "Invalid class type"
        print(repr(name), repr(cls), repr(conditions))

        if len(conditions.strip()) != 0:
            full_condition = f"[{cls} & {conditions}]"
        else:
            full_condition = f"[{cls}]"

        with onto:
            new_class = type(
                name, (eval(cls),), {"equivalent_to": eval(full_condition)}
            )
            sync_reasoner(infer_property_values=True)
        self._classes[name] = (new_class, cls)
        self.classesChanged.emit()
        return new_class


with onto:

    class Country(Thing):
        """Class representing different countries.

        Attributes:
            name (str): Name of the country
        """

        pass

    class Inventory(Thing):
        """Description of inventory balance instance for given (date, location, item).

        Attributes:
            name (str): unique ID of inventory object
            has_date (datetime.datetime): date of the inventory status
            has_location (Location): location object related to this inventory status
            has_ltype (str): location type
            has_item (Item): item on given location
            has_expiry_date (datetime.datetime): date of the item expiration
            has_available_qty (int): available quantity of the item
            has_onhand_qty (int): on-hand quantity of the item
            has_transit_qty (int): transiting quantity of the item
            has_allocated_qty (int): allocated quantity of the item
            has_suspense_qty (int): suspended quantity of the item
        """

        @classmethod
        def create(
            cls,
            date: str,
            location_id: str,
            ltype: str,
            item_id: str,
            expiry_date: str,
            available_qty: int,
            onhand_qty: int,
            transit_qty: int,
            allocated_qty: int,
            suspense_qty: int,
        ):
            date_t = convert_date(date, "%d.%m.%Y")
            expiry_date = convert_date(expiry_date, "%d.%m.%Y")

            item = onto.search_one(iri=f"{BASE_IRI}#{item_id}")
            location = onto.search_one(iri=f"{BASE_IRI}#{location_id}")

            return cls(
                f"{date.strftime('%Y:%m:%d')}-{location_id}-{item_id}",
                has_date=date_t,
                has_location=location,
                has_ltype=ltype,
                has_item=item,
                has_expiry_date=expiry_date,
                has_available_qty=available_qty,
                has_onhand_qty=onhand_qty,
                has_transit_qty=transit_qty,
                has_allocated_qty=allocated_qty,
                suspense_qty=suspense_qty,
            )

        @classmethod
        def destroy_all(cls):
            """Destroy all instances of Inventory class."""
            destroy_all(cls)

        @staticmethod
        def get_by_item(item, date):
            """Get list of inventories containing item on given date.

            Args:
                item (Item): item object to look for.
                date (datetime.datetime): date of inventory

            Returns:
                List[Item]: list of items stored at locations
            """
            return onto.search(type=Inventory, has_item=item)

    class ItemUnit(Thing):
        """Represents different packaging units of item.

        Attributes:
            name (str): unique id (item_id-unit_lvl)
            has_conversion_qty (int): number of packages inside base unit
            has_qty_uom (str): name of unit
            has_length (float): length of packaging (in meters)
            has_width (float): width of packaging (in meters)
            has_height (float): height of packaging (in meters)
            has_weight (float): weight of packaging (in kg)
        """

        @classmethod
        def create(
            cls,
            _id: str,
            conversion_qty: int,
            qty_uom: str,
            length: float,
            width: float,
            height: float,
            dim_uom: str,
            weight: float,
            weight_uom: str,
        ):
            length = convert_dim(length, dim_uom)
            width = convert_dim(width, dim_uom)
            height = convert_dim(height, dim_uom)
            weight = convert_weight(weight, weight_uom)

            return cls(
                _id,
                has_conversion_qty=conversion_qty,
                has_qty_uom=qty_uom,
                has_length=length,
                has_width=width,
                has_height=height,
                has_weight=weight,
            )

    class Item(Thing):
        """Basic description of item, including packaging units.

        Attributes:
            name (str): id of item
            has_description (str): description of items
            has_gtype (str): type of goods
            has_zone (str): required zone for storing item
            has_base_unit (ItemUnit): base packaging unit
            has_unit_levels (List[ItemUnit]): list of all different packaging units
        """

        @classmethod
        def create(
            cls,
            _id: str,
            description: str,
            gtype: str,
            zone: str,
            base_unit: ItemUnit,
            unit_levels: List[ItemUnit],
        ):
            return cls(
                _id,
                has_description=description,
                has_gtype=gtype,
                has_zone=zone,
                has_base_unit=base_unit,
                has_unit_levels=unit_levels,
            )

        @classmethod
        def destroy_all(cls):
            """Destroy all instances of Item class as well as related entities."""
            destroy_all(cls)
            destroy_all(ItemUnit)

        @staticmethod
        def get_by_locations(locations):
            """Get list of items stored at given location.

            Args:
                locations (List[Location]): list of locations to look for.

            Returns:
                List[Item]: list of items stored at locations
            """
            # TODO: Check inventory date
            values = " ".join(map(lambda x: f"<{x.iri}>", locations))
            i1 = "VALUES ?loc { " + values + " } .\n"
            i2 = f"?inv <{has_location.iri}> ?loc .\n"
            i3 = f"?inv <{has_item.iri}> ?item .\n"

            query = "SELECT DISTINCT ?item WHERE { " + i1 + i2 + i3 + " }"
            return list(default_world.sparql_query(query))

        @staticmethod
        def get_by_orders(orders):
            """Get list of items included in given orders.

            Args:
                orders (List[Order]): list of orders to search.

            Returns:
                List[Item]: list of items included in orders.
            """
            values = " ".join(map(lambda x: f"<{x.iri}>", orders))
            i1 = "VALUES ?ord { " + values + " } .\n"
            i2 = f"?ord <{has_ordered_items.iri}> ?oi .\n"
            i3 = f"?oi <{has_item.iri}> ?item .\n"

            query = "SELECT DISTINCT ?item WHERE { " + i1 + i2 + i3 + " }"
            return list(default_world.sparql_query(query))

    class Location(Thing):
        """Description of location in warehouse.

        Attributes:
            name (str): unique id of location
            has_ltype (str): type of location
            has_lclass (str): class of location
            has_lsubclass (str): subclass of location
            has_length (float): length of location
            has_width (float): width of location
            has_height (float): height of location
            has_max_weight (float): maximal weight which can location hold
            has_zone (str): zone where is location located
            has_x (float): x coordinate of location
            has_y (float): y coordinate of location
            has_z (float): z coordinate of location
            has_freq (int): frequency calculated for heat map displaying
        """

        @classmethod
        def create(
            cls,
            _id: str,
            ltype: str,
            lclass: str,
            lsubclass: str,
            length: float,
            width: float,
            height: float,
            dim_uom: str = None,
            max_weight: float = None,
            weight_uom: str = None,
            zone: str = None,
            # Params which are usually calculated later:
            x: float = None,
            y: float = None,
            z: float = None,
            freq: int = 0,
        ):
            ltype = convert_type(ltype)
            length = convert_dim(length, dim_uom)
            width = convert_dim(width, dim_uom)
            height = convert_dim(height, dim_uom)
            if max_weight:
                max_weight = convert_weight(max_weight, weight_uom)

            return cls(
                _id,
                has_ltype=ltype,
                has_lclass=lclass,
                has_lsubclass=lsubclass,
                has_length=length,
                has_width=width,
                has_height=height,
                has_max_weight=max_weight,
                has_zone=zone,
                has_x=x,
                has_y=y,
                has_z=z,
                has_freq=freq,
            )

        def set_coord(self, x: float, y: float, z: float):
            """Additionally set coordinates of the location."""
            self.has_x, self.has_y, self.has_z = x, y, z  # skipcq: PYL-W0201

        def get_2d(self):
            """Get planar coordinates of location (used for top-down view)."""
            return (self.has_x, self.has_y)

        @classmethod
        def destroy_all(cls):
            """Destroy all instances of Location class."""
            destroy_all(cls)

        @staticmethod
        def get_by_orders(orders):
            """Get list of locations which are potentially accessed by given orders.

            Args:
                locations (List[Order]): list of locations to inspect

            Returns:
                List[Location]: list of locations containing ordered items
            """
            # TODO: speed up this query (reverse property???)
            values = " ".join(map(lambda x: f"<{x.iri}>", orders))
            i1 = "VALUES ?ord { " + values + " } .\n"
            i2 = f"?ord <{has_ordered_items.iri}> ?oi .\n"
            i3 = f"?oi <{has_item.iri}> ?item .\n"
            i4 = f"?inv <{has_item.iri}> ?item .\n"
            i5 = f"?inv <{has_location.iri}> ?loc .\n"

            query = "SELECT DISTINCT ?loc WHERE { " + i1 + i2 + i3 + i4 + i5 + " }"
            return list(default_world.sparql_query(query))

        @staticmethod
        def get_by_items(items):
            """Get list of locations storing given items.

            Args:
                items (List[Item]): list of items to locate items.

            Returns:
                List[Location]: list of locations storing items
            """
            values = " ".join(map(lambda x: f"<{x.iri}>", items))
            i1 = "VALUES ?item { " + values + " } .\n"
            i2 = f"?inv <{has_item.iri}> ?item .\n"
            i3 = f"?inv <{has_location.iri}> ?loc .\n"

            query = "SELECT DISTINCT ?loc WHERE { " + i1 + i2 + i3 + " }"
            return list(default_world.sparql_query(query))

    class OrderedItem(Thing):
        """Description of item instance in order.

        Attributes:
            name (str): id of object (ordered_id-item_id)
            has_item (Item): item object instantiated by this order
            has_requested_qty (int): requested amount of item inside ordered
            has_total_qty (int): amount of item provided inside order
            qty_uom (int): unit of measure of quantities
        """

        pass

    class Order(Thing):
        """Description of single order from warehouse.

        Attributes:
            name (str): id of the order
            has_direction (str): outbound/inbound
            has_country (str): Country object representing shipping destination
            has_delivery_date (datetime.datetime): requested delivery date
            has_s_ship_date (datetime.datetime): scheduled sipping date
            has_a_ship_date (datetime.datetime): actual sipping date
            has_line_num (int): ERP order line number
            has_ordered_items (List[OrderedItem]): list of item instances inside order
        """

        @classmethod
        def create(
            cls,
            _id: str,
            direction: str,
            country_id: str,
            delivery_date: str,
            s_ship_date: str,
            a_ship_date: str,
            line_num: int,
            item_id: str,
            requested_qty: int,
            total_qty: int,
            qty_uom: str,
        ):
            _id = str(_id)
            # Convert to datetime
            delivery_date = convert_date(delivery_date, "%d.%m.%Y")
            s_ship_date = convert_date(s_ship_date, "%d.%m.%Y")
            a_ship_date = convert_date(a_ship_date, "%d.%m.%Y")

            country = onto.search_one(iri=f"{BASE_IRI}#{country_id}")
            if country is None:
                country = Country(country_id)

            item = onto.search_one(iri=f"{BASE_IRI}#{item_id}")
            oi = OrderedItem(
                f"{_id}-{item_id}",
                has_item=item,
                has_requested_qty=requested_qty,
                has_total_qty=total_qty,
                has_qty_uom=qty_uom,
            )

            return cls(
                _id,
                has_direction=direction,
                has_country=country,
                has_delivery_date=delivery_date,
                has_s_ship_date=s_ship_date,
                has_a_ship_date=a_ship_date,
                has_line_num=line_num,
                has_ordered_items=[oi],
            )

        def add_item(
            self, item_id: str, requested_qty: int, total_qty: int, qty_uom: str
        ):
            """Create and add item instance into order."""
            item = onto.search_one(iri=f"{BASE_IRI}#{item_id}")
            oi = OrderedItem(
                f"{self.name}-{item_id}",
                has_item=item,
                has_requested_qty=requested_qty,
                has_total_qty=total_qty,
                has_qty_uom=qty_uom,
            )
            self.has_ordered_items.append(oi)

        @classmethod
        def destroy_all(cls):
            """Destroy all instances of Order class as well as related entities."""
            destroy_all(cls)
            destroy_all(OrderedItem)

        @staticmethod
        def get_by_items(items):
            """Get list of orders which contains given items.

            Args:
                items (List[Item]): list of items to look for.

            Returns:
                List[Order]: list of orders containing at leas one of the provided items
            """
            values = " ".join(map(lambda x: f"<{x.iri}>", items))
            i1 = "VALUES ?item { " + values + " } .\n"
            i2 = f"?oi <{has_item.iri}> ?item .\n"
            i3 = f"?ord <{has_ordered_items.iri}> ?oi .\n"

            query = "SELECT DISTINCT ?ord WHERE { " + i1 + i2 + i3 + " }"
            return list(default_world.sparql_query(query))

        @staticmethod
        def get_by_locations(locations):
            """Get list of orders which potentially access given locations.

            Args:
                locations (List[Location]): list of locations to inspect

            Returns:
                List[Order]: list of orders containing items stored at given locations
            """
            values = " ".join(map(lambda x: f"<{x.iri}>", locations))
            i1 = "VALUES ?loc { " + values + " } .\n"
            i2 = f"?inv <{has_location.iri}> ?loc .\n"
            i3 = f"?inv <{has_item.iri}> ?item .\n"
            i4 = f"?oi <{has_item.iri}> ?item .\n"
            i5 = f"?ord <{has_ordered_items.iri}> ?oi .\n"

            query = "SELECT DISTINCT ?ord WHERE { " + i1 + i2 + i3 + i4 + i5 + " }"
            return list(default_world.sparql_query(query))

    # Order properties
    class has_direction(Order >> str, FunctionalProperty):
        """Direction of Order."""

    class has_country(Order >> Country, FunctionalProperty):
        """Country of destination of Order."""

    class has_delivery_date(Order >> datetime.datetime, FunctionalProperty):
        """Delivery date of Order."""

    class has_s_ship_date(Order >> datetime.datetime, FunctionalProperty):
        """Scheduled shipping date of Order."""

    class has_a_ship_date(Order >> datetime.datetime, FunctionalProperty):
        """Actual shipping date of Order."""

    class has_line_num(Order >> int, FunctionalProperty):
        """Line number of Order."""

    class has_ordered_items(Order >> OrderedItem):
        """List of OrderedItem (instances of Item) inside Order."""

    # OrderedItem properties
    class has_item(ObjectProperty, FunctionalProperty):
        """Item which is instantiated."""

        domain = [OrderedItem, Inventory]
        range = [Item]

    class in_order(OrderedItem >> Order, FunctionalProperty):
        """Pointer to Order which contains this OrderedItem."""

        inverse_property = has_ordered_items

    class has_requested_qty(OrderedItem >> int, FunctionalProperty):
        """Requested quantity of Item."""

    class has_total_qty(OrderedItem >> int, FunctionalProperty):
        """Total quantity of Item."""

    class has_qty_uom(DataProperty, FunctionalProperty):
        """Quantity unit of measure used for total_qty and requested_qty."""

        domain = [OrderedItem, ItemUnit]
        range = [str]

    # ItemUnit properties
    class has_conversion_qty(ItemUnit >> int, FunctionalProperty):
        """Conversion quantity of ItemUnit."""

    class has_weight(ItemUnit >> float, FunctionalProperty):
        """Conversion quantity of ItemUnit."""

    # Item properties
    class in_ordered_item(Item >> OrderedItem):
        """List of OrderedItems (Item instantiations) where Item appears."""

        inverse_property = has_item

    class has_description(Item >> str, FunctionalProperty):
        """Description of Item."""

    class has_gtype(Item >> str, FunctionalProperty):
        """Good type of Item."""

    class has_zone(DataProperty, FunctionalProperty):
        """Zone required by Item or Zone of Location."""

        domain = [Item, Location]
        range = [str]

    class has_base_unit(Item >> ItemUnit, FunctionalProperty):
        """Base ItemUnit of Item."""

    class has_unit_levels(Item >> ItemUnit):
        """List of ItemUnits (unit levels) of Item."""

    # Location properties
    class has_ltype(DataProperty, FunctionalProperty):
        """Location type."""

        domain = [Location, Inventory]
        range = [str]

    class has_lclass(Location >> str, FunctionalProperty):
        """Location class."""

    class has_lsubclass(Location >> str, FunctionalProperty):
        """Location subclass."""

    class has_length(DataProperty, FunctionalProperty):
        """Length of Location/ItemUnit."""

        domain = [Location, ItemUnit]
        range = [float]

    class has_width(DataProperty, FunctionalProperty):
        """Width of Location/ItemUnit."""

        domain = [Location, ItemUnit]
        range = [float]

    class has_height(DataProperty, FunctionalProperty):
        """Height of Location/ItemUnit."""

        domain = [Location, ItemUnit]
        range = [float]

    class has_max_weight(Location >> float, FunctionalProperty):
        """Max weight which Location can hold."""

    class has_freq(Location >> int, FunctionalProperty):
        """Frequency calculated for the location."""

    class has_x(Location >> float, FunctionalProperty):
        """x coordinate of Location."""

    class has_y(Location >> float, FunctionalProperty):
        """y coordinate of Location."""

    class has_z(Location >> float, FunctionalProperty):
        """z coordinate of Location."""

    # Inventory properties
    class has_date(Inventory >> datetime.datetime, FunctionalProperty):
        """Date of Inventory report."""

    class has_location(Inventory >> Location, FunctionalProperty):
        """Location described by Inventory."""

    class has_expiry_date(Inventory >> datetime.datetime, FunctionalProperty):
        """Expiry date of Item in Inventory."""

    class has_available_qty(Inventory >> int, FunctionalProperty):
        """Available quantity of Item."""

    class has_onhand_qty(Inventory >> int, FunctionalProperty):
        """On-hand quantity of Item."""

    class has_transit_qty(Inventory >> int, FunctionalProperty):
        """Quantity in transit of Item."""

    class has_allocated_qty(Inventory >> int, FunctionalProperty):
        """Allocated quantity of Item."""

    class has_supsense_qty(Inventory >> int, FunctionalProperty):
        """Suspense quantity of Item."""


# sync_reasoner(infer_property_values=True)

# SQLite3
# default_world.graph.db
# default_world.graph.execute
