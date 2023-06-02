"""This module allows getting information and changing Alma item records"""
import os
from typing import Optional, ClassVar, Literal
import logging
from ..record import Record, check_error, XmlData
import almapiwrapper.inventory as inventory
from lxml import etree
import re


class Item(Record):
    """Class representing an item.

    There are several possibilities to get item information:
        - 'get_items' method of :class:`almapiwrapper.inventory.Holding` object
        - Item(mms_id, holding_id, item_id, zone, env)
        - Item(holding=:class:`almapiwrapper.inventory.Holding`, item_id=item_id)
        - Item(barcode='barcode', zone='zone', env='env')

    Create an item:
        - Item(holding=:class:`almapiwrapper.inventory.Holding`, data=`almapiwrapper.record.XmlData`, create_item=True)

    :ivar item_id: numerical ID of the item
    :ivar zone: zone of the record
    :ivar env: environment of the entity: 'P' for production and 'S' for sandbox
    :ivar holding: :class:`almapiwrapper.inventory.Holding` object
    :ivar data: :class:`almapiwrapper.record.XmlData` object, useful to force
        update a record from a backup
    :param barcode: string with barcode of the item
    :param mms_id: bib record mms_id
    :param holding_id: holding record ID
    :param create_item: when True, create a new item
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
        self.error_msg = None
        self._data = data

        if holding_id is not None and mms_id is not None and holding is None:
            holding = inventory.Holding(mms_id, holding_id, zone, env)

        self.holding = holding
        self.item_id = item_id
        self._barcode = barcode
        self.area = 'Bibs'
        self.format = 'xml'

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
        elif barcode is not None and create_item is False and data is None:
            data = self._fetch_data(barcode)
            if data is not None:
                self.data = data
                self.item_id = self.get_item_id()

        # Fetch the item from IDs of item, holding and bibliographic record
        elif self.item_id is not None and mms_id is not None and holding_id is not None and data is None:
            self.holding = inventory.Holding(mms_id, holding_id, self.zone, self.env)
            if self.holding.error is True:
                self.error = True
            self.data = self._fetch_data()

        # Fetch item through 'item_id' and holding
        elif self.item_id is not None and holding is not None and data is None:
            self.data = self._fetch_data()

        # The data provided does not allow to initialize an item
        elif data is None:
            logging.error('Missing information to construct an Item')
            self.error = True

    def __repr__(self):
        """Get a string representation of the object. Useful for logs.

        :return: string
        """
        if self._holding is None and self._barcode is not None:
            return f"{self.__class__.__name__}(barcode='{self._barcode}', " \
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
            r = self._api_call('get',
                               self.api_base_url_items,
                               params={'item_barcode': barcode},
                               headers=self._get_headers())
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
            r = self._api_call('get',
                               f'{self.api_base_url_bibs}/{self.bib.mms_id}/holdings/{self.holding.holding_id}'
                               f'/items/{self.item_id}',
                               headers=self._get_headers())

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
        r = self._api_call('post',
                           f'{self.api_base_url_bibs}/{self.bib.mms_id}/holdings/{self.holding.holding_id}/items',
                           headers=self._get_headers(),
                           data=etree.tostring(data))

        if r.ok is True:
            self.data = XmlData(r.content)
            self.item_id = self.get_item_id()
            logging.info(f'{repr(self)}: item created')
        else:
            self._handle_error(r, 'unable to create the new item')

    @check_error
    def get_item_id(self) -> str:
        """get_item_id() -> str
        Fetch the item ID in the xml data of 'data' attribute. Useful for creating a new item.

        :return: item id
        """
        return self.data.find('.//pid').text

    @check_error
    def get_holding_id(self) -> str:
        """get_holding_id() -> str:
        Fetch holding ID

        :return: holding ID
        """

        return self.data.find('.//holding_id').text

    @check_error
    def get_mms_id(self) -> str:
        """get_mms_id(self) -> str
        Fetch IZ MMS ID

        :return: IZ MMS ID
        """

        return self.data.find('.//mms_id').text

    @check_error
    def get_nz_mms_id(self) -> Optional[str]:
        """get_mms_id(self) -> Optional[str]
        Fetch NZ MMS ID

        :return: NZ MMS ID
        """

        nz_number_fields = self.data.findall('.//network_number')
        for field in nz_number_fields:
            m = re.match(r'\(EXLNZ.+?\)(\d+)', field.text)
            if m is not None:
                return m.group(1)

        logging.warning('{repr(self)}: Record not linked with NZ, no NZ MMS ID available')

    @property
    def bib(self) -> inventory.IzBib:
        """
        Property of the item returning the bibliographic record

        :return: IzBib
        """
        if self.holding is not None:
            return self.holding.bib

    @property
    def holding(self) -> Optional[inventory.Holding]:
        """holding(self) -> Optional[inventory.Holding]
        Property of the item returning the :class:`almapiwrapper.inventory.Holding` object
        related to the item

        :return: :class:`almapiwrapper.inventory.Holding`
        """
        if self._holding is None and self.error is False:
            holding_id = self.get_holding_id()
            mms_id = self.get_mms_id()
            self._holding = inventory.Holding(mms_id, holding_id, self.zone, self.env)

        # To force fetching holding data
        # _ = self._holding.data

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
        """save(self) -> 'Item'
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
        r = self._api_call('put',
                           f'{self.api_base_url_bibs}/{self.bib.mms_id}/holdings/{self.holding.holding_id}/'
                           f'items/{self.item_id}',
                           data=bytes(self),
                           headers=self._get_headers())

        if r.ok is True:
            self.data = XmlData(r.content)
            logging.info(f'{repr(self)}: item data updated')
        else:
            self._handle_error(r, 'unable to update item data')

        return self

    @check_error
    def delete(self) -> None:
        """delete(self) -> None
        Delete an item.

        :return: None
        """
        r = self._api_call('delete',
                           f'{self.api_base_url_bibs}/{self.bib.mms_id}/holdings/{self.holding.holding_id}'
                           f'/items/{self.item_id}',
                           headers=self._get_headers())
        if r.ok is True:
            logging.info(f'{repr(self)} deleted')
        else:
            self._handle_error(r, 'unable to delete the item')

    @property
    @check_error
    def library(self) -> Optional[str]:
        """library(self) -> Optional[str]
        Property of the holding returning the library code

        :return: library code
        """
        library = self.data.find('.//item_data/library')
        if library is None:
            logging.warning(f'{repr(self)}: no library in the item')
            return
        return library.text

    @library.setter
    @check_error
    def library(self, library_code: str) -> None:
        """library(self, library_code: str) -> None
        This setter is able to update the 852$b of the holding. But the field should already exist.

        :param library_code: code of the library to insert in 852$b field

        :return: None
        """
        library = self.data.find('.//item_data/library')
        if library is None:
            logging.error(f'{repr(self)}: no library field -> not possible to update it')
            self.error = True
        else:
            logging.info(f'{repr(self)}: library changed from "{library.text}" to "{library_code}"')
            library.text = library_code
            library.attrib.pop('desc', None)

    @property
    @check_error
    def location(self) -> Optional[str]:
        """location(self) -> Optional[str]
        Property of the holding returning the library code

        :return: library code
        """
        location = self.data.find('.//item_data/location')
        if location is None:
            logging.warning(f'{repr(self)}: no location in the item')
            return
        return location.text

    @location.setter
    @check_error
    def location(self, location_code: str) -> None:
        """location(self, location_code: str) -> None
        This setter is able to update the 852$c of the holding. But the field should already exist.

        :param location_code:

        :return: None
        """
        location = self.data.find('.//item_data/location')
        if location is None:
            logging.error(f'{repr(self)}: no location field -> not possible to update it')
        else:
            logging.info(f'{repr(self)}: location changed from "{location.text}" to "{location_code}"')
            location.text = location_code
            location.attrib.pop('desc', None)

    @staticmethod
    def get_data_from_disk(mms_id: str, holding_id: str, item_id: str, zone: str) -> Optional[XmlData]:
        """get_data_from_disk(mms_id, holding_id, item_id, zone)
        Fetch the data of the described record

        :param mms_id: bib record mms_id
        :param holding_id: holding record ID
        :param item_id: numerical ID of the item
        :param zone: zone of the record

        :return: :class:`almapiwrapper.record.XmlData` or None
        """
        if os.path.isdir(f'records/{zone}_{mms_id}') is False:
            return

        # Fetch all available filenames related to this record
        file_names = sorted([file_name for file_name in os.listdir(f'records/{zone}_{mms_id}')
                             if file_name.startswith(f'item_{holding_id}_{item_id}') is True])

        if len(file_names) == 0:
            return

        return XmlData(filepath=f'records/{zone}_{mms_id}/{file_names[-1]}')

    @check_error
    def scan_in(self, library: str, circ_desk: str) -> 'Item':
        """scan_in(self) -> 'Item'
        Scan in an item

        :return: Item
        """
        r = self._api_call('post',
                           f'{self.api_base_url_bibs}/{self.bib.mms_id}/holdings/{self.holding.holding_id}/'
                           f'items/{self.item_id}',
                           params={'op': 'scan', 'library': library, 'circ_desk': circ_desk},
                           headers=self._get_headers())
        if r.ok is True:
            logging.info(f'{repr(self)}: scanned in')
        else:
            self._handle_error(r, 'unable to "scan in" the item')

        return self
