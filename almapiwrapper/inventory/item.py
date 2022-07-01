"""This module allows getting information and changing Alma item records"""

from typing import Optional, ClassVar, Literal
import logging
import requests
from ..record import Record, check_error, XmlData
import almapiwrapper.inventory as inventory
from lxml import etree


class Item(Record):
    """Class representing an item

    There are several possibilities to build an item:
        - 'get_items' method of :class:`almapiwrapper.inventory.Holding` object
        - Item(mms_id, holding_id, item_id, zone, env)
        - Item(holding=Holding, item_id=item_id)
        - Item(barcode='barcode', zone='zone', env='env')

        Instead of providing the item_id it is possible to provide the barcode.

    :ivar mms_id: initial value: bib record mms_id
    :ivar holding_id: initial value: holding record ID
    :ivar item_id: numerical ID of the item
    :ivar zone: initial value: zone of the record
    :ivar env: initial value: environment of the entity: 'P' for production and 'S' for sandbox
    :ivar holding: :class:`almapiwrapper.inventory.Holding` object
    :ivar barcode: string with barcode of the item
    :ivar data: initial value: :class:`almapiwrapper.record.XmlData` object, useful to force
        update a record from a backup
    :ivar create_item: when True, create a new item
    """

    api_base_url_items: ClassVar[str] = f'{Record.api_base_url}/items'
    api_base_url_bibs: ClassVar[str] = f'{Record.api_base_url}/bibs'

    def __init__(self,
                 mms_id: Optional[str] = None,
                 holding_id: Optional[str] = None,
                 item_id: Optional[str] = None,
                 zone: Optional[str] = None,
                 env: Optional[Literal['P', 'S']] = 'P',
                 holding: Optional[inventory.Holding] = None,
                 barcode: Optional[str] = None,
                 data: Optional[etree.Element] = None,
                 create_item: Optional[bool] = False) -> None:
        """Construct an item.
        """
        self.error = False
        self._data = data
        self.holding = holding
        self.item_id = item_id
        self._barcode = barcode
        self.area = 'Bibs'

        # Set 'env' and 'zone' either from holding data either from parameters
        if holding is not None:
            self.zone = holding.zone
            self.env = holding.env
        else:
            self.zone = zone
            self.env = env

        # Create a new item if 'create_item' parameter is True
        if self.item_id is None and data is not None and holding is not None and create_item is True:
            self._create_item(data)

        # Fetch the item from the barcode, zone and env must be available
        elif barcode is not None and create_item is False:
            data = self._fetch_data(barcode)
            if data is not None:
                self.data = data
                self.item_id = self.get_item_id()

        # Fetch the item from IDs of item, holding and bibliographic record
        elif self.item_id is not None and mms_id is not None and holding_id is not None:
            self.holding = inventory.Holding(mms_id, holding_id, self.zone, self.env)
            if self.holding.error is True:
                self.error = True
            self.data = self._fetch_data()

        # Fetch item through 'item_id' and holding
        elif self.item_id is not None and holding is not None:
            self.data = self._fetch_data()

        # The data provided does not allow to initialize an item
        else:
            logging.error('Missing information to construct an Item')
            self.error = True

    def __repr__(self):
        """Get a string representation of the object. Useful for logs.
        :return: string
        """
        if self._holding is None and self._barcode is not None:
            return f"{self.__class__.__name__}(barcode='{self._barcode}' " \
                   f"zone='{self.zone}', env='{self.env}')"
        return f"{self.__class__.__name__}('{self.bib.mms_id}', '{self.holding.holding_id}'," \
               f"'{self.item_id}', '{self.zone}', '{self.env}')"

    def _fetch_data(self, barcode: Optional[str] = None) -> Optional[XmlData]:
        """
        Fetch item data and store it in 'data' attribute
        :param barcode: barcode of the item
        :return: None
        """
        if barcode is not None:
            r = requests.get(self.api_base_url_items,
                             params={'item_barcode': barcode},
                             headers=self._get_headers(data_format='xml'))
            if r.ok is True:
                logging.info(f"{repr(self)}: item data fetched with barcode '{barcode}'")
                return XmlData(r.content)
            else:
                self._handle_error(r, f"unable to get item data from barcode '{barcode}'")
                self.error = True
                return

            # # Fetch holding
            # self.holding = inventory.Holding(self.data.find('.//mms_id').text,
            #                                  self.data.find('.//holding_id').text,
            #                                  self.zone, self.env)

        # No barcode provided
        else:
            r = requests.get(f'{self.api_base_url_bibs}/{self.bib.mms_id}/holdings/{self.holding.holding_id}'
                             f'/items/{self.item_id}',
                             headers=self._get_headers(data_format='xml'))

            if r.ok is True:

                logging.info(f'{repr(self)}: item data available')
                return XmlData(r.content)
            else:
                self._handle_error(r, 'unable to fetch item data')

    def _create_item(self, data: etree.Element):
        """
        Create an item to the holding with the provided data.
        :param data: item data
        :return: Item
        """
        r = requests.post(f'{self.api_base_url_bibs}/{self.bib.mms_id}/holdings/{self.holding.holding_id}/items',
                          headers=self._get_headers(data_format='xml'),
                          data=etree.tostring(data))

        if r.ok is True:
            self.data = XmlData(r.content)
            self.item_id = self.get_item_id()
            logging.info(f'{repr(self)}: item created')
        else:
            self._handle_error(r, 'unable to create the new item')

    def get_item_id(self) -> str:
        """
        Fetch the item ID in the xml data of 'data' attribute. Useful for creating a new item.
        """
        return self.data.find('.//pid').text

    @property
    def bib(self) -> inventory.IzBib:
        """
        Property of the item returning the bibliographic record
        :return: IzBib
        """
        if self.holding is not None:
            return self.holding.bib

    @property
    def holding(self) -> inventory.Holding:
        """holding(self) -> 'inventory.Holding'
        Property of the item returning the :class:`almapiwrapper.inventory.Holding` object
        related to the item
        :return: :class:`almapiwrapper.inventory.Holding`
        """
        if self._holding is None and self.error is False:
            holding_id = self.data.find('.//holding_id').text
            mms_id = self.data.find('.//mms_id').text
            self._holding = inventory.Holding(mms_id, holding_id, self.zone, self.env)

        # To force fetching holding data
        _ = self._holding.data

        if self._holding.error is True:
            self.error = True
            return

        return self._holding

    @holding.setter
    def holding(self, holding: inventory.Holding) -> None:
        """Property of the item containing the holding
        :return: None"""
        self._holding = holding

    @property
    @check_error
    def barcode(self) -> Optional[str]:
        """barcode(self) -> Optional[str]
        Property of the item returning the barcode
        :return: library code
        """
        barcode_field = self.data.find('.//barcode')
        if barcode_field is None:
            logging.warning(f'{repr(self)}: no barcode in the item')
            return
        return barcode_field.text

    @barcode.setter
    @check_error
    def barcode(self, barcode: str) -> None:
        """barcode(self, barcode: str) -> None
        This setter is able to update the barcode of the item. But the field should already exist.
        :param barcode: barcode of the item
        :return: None
        """
        barcode_field = self.data.find('.//barcode')
        if barcode_field is None:
            logging.error(f'{repr(self)}: no barcode field in the item -> not possible to update it')
            self.error = True
        else:
            logging.info(f'{repr(self)}: barcode changed from "{barcode_field.text}" to "{barcode}"')
            barcode_field.text = barcode

    @check_error
    def save(self) -> 'Item':
        """
        Save a record item in the 'records' folder. Versioning is supported. A suffix is added to the file path.
        Example: records/UBS_9963486250105504/item_22314215800005504_23314215790005504_01.xml
        :return: Item
        """
        filepath = f'records/{self.zone}_{self.bib.mms_id}/item_{self.holding.holding_id}_{self.item_id}.xml'
        self._save_from_path(filepath)
        return self

    @check_error
    def update(self) -> 'Item':
        """update(self) -> 'Item'
        Update items data.
        :return: Item
        """
        r = requests.put(f'{self.api_base_url_bibs}/{self.bib.mms_id}/holdings/{self.holding.holding_id}/'
                         f'items/{self.item_id}',
                         data=bytes(self),
                         headers=self._get_headers(data_format='xml'))

        if r.ok is True:
            self.data = XmlData(r.content)
            logging.info(f'{repr(self)}: item data updated')
        else:
            self._handle_error(r, 'unable to update item data')

        return self

    @check_error
    def delete(self) -> None:
        """delete(self) -> None
        Suppress an item.
        :return: None
        """
        r = requests.delete(f'{self.api_base_url_bibs}/{self.bib.mms_id}/holdings/{self.holding.holding_id}'
                            f'/items/{self.item_id}',
                            headers=self._get_headers(data_format='xml'))
        if r.ok is True:
            logging.info(f'{repr(self)} deleted')
        else:
            self._handle_error(r, 'unable to delete the item')
