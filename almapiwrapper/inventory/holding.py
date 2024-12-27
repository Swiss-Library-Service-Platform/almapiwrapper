"""This module allows getting information and changing Alma holding records"""

from typing import Optional, Literal, List, ClassVar, Union
import logging
from ..record import Record, check_error, XmlData
import almapiwrapper.inventory as inventory
from lxml import etree
import os


class Holding(Record):
    """
    Class representing a holding object. Holdings are only in the IZ.

    Several possibilities for building holdings:
    - 'get_holdings' method of IzBib object
    - Holding(mms_id, holding_id, zone, env)
    - Holding(bib=BibIz, holding_id=holding_id)

    if no 'holding_id' is provided, but 'data' is provided and create_holding is True, then
    it creates a new holding.


    :ivar holding_id: holding ID
    :ivar zone: zone of the record
    :ivar env: environment of the entity: 'P' for production and 'S' for sandbox
    :ivar bib: class:`almapiwrapper.inventory.IzBib` object
    :ivar data: :class:`almapiwrapper.record.XmlData` or `etree.Element` object,
    useful to force update a record from a backup
    :param mms_id: record mms_id
    :param create_holding: boolean, if True try to create a new holding (if no 'holding_id' is provided)
    """

    api_base_url_bibs: ClassVar[str] = f'{Record.api_base_url}/bibs'

    def __init__(self,
                 mms_id: Optional[str] = None,
                 holding_id: Optional[str] = None,
                 zone: Optional[str] = None,
                 env: Optional[Literal['P', 'S']] = 'P',
                 bib: Optional[inventory.IzBib] = None,
                 data: Optional[Union['XmlData', etree.Element]] = None,
                 create_holding: Optional[bool] = False) -> None:
        """
        Construct a holding record. Several possibilities for building holdings:
        - 'get_holdings' method of IzBib object
        - Holding(mms_id, holding_id, zone, env)
        - Holding(bib=BibIz, holding_id=holding_id)

        if no 'holding_id' is provided, but 'data' is provided and create_holding is True, then
        it creates a new holding.
        """
        self._items = None
        self.error = False
        self.error_msg = None
        self._data = None
        self.area = 'Bibs'
        self.format = 'xml'
        self.bib = bib
        self.holding_id = holding_id

        if self.bib is not None:
            self.zone = self.bib.zone
            self.env = self.bib.env

        else:
            self.zone = zone
            self.env = env
            self.bib = inventory.IzBib(mms_id, self.zone, self.env)

            # If there is an error in the bibliographic record, it is spread out in the holding record
            if self.bib.error is True:
                self.error = True

        # Create a new holding if 'create_holding' is True
        if self.holding_id is None and data is not None and create_holding is True:
            if data.__class__.__name__ == '_Element':
                data = XmlData(etree.tostring(data))
            self._create_holding(data)

    def __repr__(self) -> str:
        """Get a string representation of the object. Useful for logs.

        :return: string
        """
        return f"{self.__class__.__name__}('{self.bib.mms_id}', '{self.holding_id}', '{self.zone}', '{self.env}')"

    def _fetch_data(self) -> Optional[XmlData]:
        """Fetch holding data via API. Store the data in the 'data' attribute.

        :return: None
        """
        r = self._api_call('get',
                           f'{self.api_base_url_bibs}/{self.bib.mms_id}/holdings/{self.holding_id}',
                           headers=self._get_headers())

        if r.ok is True:
            logging.info(f'{repr(self)}: holding data available')
            return XmlData(r.content)
        else:
            self._handle_error(r, 'unable to fetch holding data')

    def _create_holding(self, data: etree.Element) -> None:
        """Create a holding and link it to the provided bibliographic record

        :param data: data used to create the holding

        :return: None
        """
        r = self._api_call('post',
                           f'{self.api_base_url_bibs}/{self.bib.mms_id}/holdings',
                           headers=self._get_headers(),
                           data=bytes(data))

        if r.ok is True:
            self.data = XmlData(r.content)
            self.holding_id = self.get_holding_id()
            logging.info(f'{repr(self)}: holding created')
        else:
            self._handle_error(r, 'unable to create the new holding')

    @check_error
    def get_holding_id(self) -> str:
        """get_holding_id(self) -> str
        Fetch holding ID in the data of 'data' attribute.

        Useful for creating a new holding.

        :return: str with holding id
        """
        return self.data.find('.//holding_id').text

    @check_error
    def save(self) -> 'Holding':
        """save(self) -> 'Holding'
        Save holding in a folder for each MMS ID.
        Example: records/UBS_9963486250105504/hol_22314215780005504_01.xml

        :return: Holding
        """
        filepath = f'records/{self.zone}_{self.bib.mms_id}/hol_{self.holding_id}.xml'
        self._save_from_path(filepath)
        return self

    @check_error
    def update(self) -> 'Holding':
        """update(self) -> 'Holding'
        Update data of a holding.

        :return: Holding
        """
        r = self._api_call('put',
                           f'{self.api_base_url_bibs}/{self.bib.mms_id}/holdings/{self.holding_id}',
                           data=etree.tostring(self.data),
                           headers=self._get_headers())

        if r.ok is True:
            self.data = XmlData(r.content)
            logging.info(f'{repr(self)}: holding data updated')
        else:
            self._handle_error(r, 'unable to update holding data')

        return self

    @check_error
    def delete(self, force: Optional[bool] = False) -> None:
        """delete(self, force: Optional[bool] = False) -> None
        Delete holding

        :return: None
        """
        if force is True:
            self.delete_items()

        r = self._api_call('delete',
                           f'{self.api_base_url_bibs}/{self.bib.mms_id}/holdings/{self.holding_id}',
                           headers=self._get_headers())
        if r.ok is True:
            logging.info(f'{repr(self)} deleted')
        else:
            self._handle_error(r, 'unable to delete the holding')

    @check_error
    def get_items(self) -> List['inventory.Item']:
        """get_items(self) -> List['inventory.Item']
        This method is used to retrieve the list of items and loads
        the xml data of these items. To avoid reloading this information,
        the items references are stored in the private attribute '_items'.

        :return: list of :class:`almapiwrapper.bib.Item` objects
        """
        # Check if items have been already fetched
        if self._items is not None:
            return self._items

        # Fetch the item's data through apis
        r = self._api_call('get',
                           f'{self.api_base_url_bibs}/{self.bib.mms_id}/holdings/{self.holding_id}/items',
                           params={'limit': '100'},
                           headers=self._get_headers())

        if r.ok is True:
            root = etree.fromstring(r.content, parser=self.parser)
        else:
            self._handle_error(r, 'unable to fetch items')
            return []

        items_data = root.findall('.//item_data')
        if len(items_data) > 99:
            logging.warning(f'{repr(self)}: at least 100 items, risk of missing items')

        # No item found
        if len(items_data) == 0:
            logging.warning(f'{repr(self)}: no item found')
            self._items = []
            return self._items

        logging.info(f'{repr(self)}: {len(items_data)} items fetched')

        # Fetch items one by one
        self._items = []
        for item in items_data:
            item_id = item.find('.//pid').text
            self._items.append(inventory.Item(holding=self, item_id=item_id))

        return self._items

    @check_error
    def delete_items(self) -> None:
        """delete_items(self) -> None
        Delete all items of the holding

        :return: None
        """
        for item in self.get_items():
            item.delete()

    @property
    @check_error
    def library(self) -> Optional[str]:
        """library(self) -> Optional[str]
        Property of the holding returning the library code

        :return: str containing library code
        """
        library = self.data.find('.//datafield[@tag="852"]/subfield[@code="b"]')
        if library is None:
            logging.warning(f'{repr(self)}: no library in the holding')
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
        library = self.data.find('.//datafield[@tag="852"]/subfield[@code="b"]')
        if library is None:
            logging.error(f'{repr(self)}: no library field in the holding -> not possible to update it')
            self.error = True
        else:
            logging.info(f'{repr(self)}: library changed from "{library.text}" to "{library_code}"')
            library.text = library_code

    @property
    @check_error
    def location(self) -> Optional[str]:
        """location(self) -> Optional[str]
        Property of the holding returning the library code

        :return: str containing library code
        """
        location = self.data.find('.//datafield[@tag="852"]/subfield[@code="c"]')
        if location is None:
            logging.warning(f'{repr(self)}: no location in the holding')
            return
        return location.text

    @location.setter
    @check_error
    def location(self, location_code: str) -> None:
        """location(self, location_code: str) -> None
        This setter is able to update the 852$c of the holding. But the field should already exist.

        :param location_code: location code to set to the holding

        :return: None
        """
        location = self.data.find('.//datafield[@tag="852"]/subfield[@code="c"]')
        if location is None:
            logging.error(f'{repr(self)}: no location field in the holding -> not possible to update it')
        else:
            logging.info(f'{repr(self)}: location changed from "{location.text}" to "{location_code}"')
            location.text = location_code

    @property
    @check_error
    def callnumber(self) -> Optional[str]:
        """callnumber(self) -> Optional[str]
        Property of the holding returning the callnumber

        :return: str containing callnumber
        """
        field852 = self.data.find('.//datafield[@tag="852"]')
        if field852 is None:
            return None

        callnumber_field = field852.find('./subfield[@code="j"]')

        if callnumber_field is None:
            callnumber_field = field852.find('./subfield[@code="h"]')

        if callnumber_field is None:
            logging.warning(f'{repr(self)}: no callnumber field in the holding')
            return None

        return callnumber_field.text

    @callnumber.setter
    @check_error
    def callnumber(self, callnumber_txt: str) -> None:
        """callnumber(self, callnumber_txt: str) -> None
        This setter is able to update the 852$j or 852$h of the holding. But the field should already exist.

        :param callnumber_txt: text of the callnumber to be set in j or h subfield

        :return: None
        """
        field852 = self.data.find('.//datafield[@tag="852"]')
        if field852 is None:
            return

        callnumber_field = field852.find('./subfield[@code="j"]')

        if callnumber_field is None:
            callnumber_field = field852.find('./subfield[@code="h"]')

        if callnumber_field is None:
            logging.error(f'{repr(self)}: no callnumber field in the holding -> not possible to update it')
            return

        logging.info(f'{repr(self)}: callnumber changed from "{callnumber_field.text}" to "{callnumber_txt}"')
        callnumber_field.text = callnumber_txt

    @staticmethod
    def get_data_from_disk(mms_id: str, holding_id: str, zone: str) -> Optional[XmlData]:
        """get_data_from_disk(mms_id, holding_id, zone)
        Fetch the data of the described record

        :param mms_id: bib record mms_id
        :param holding_id: holding record ID
        :param zone: zone of the record

        :return: :class:`almapiwrapper.record.XmlData` or None
        """
        if os.path.isdir(f'records/{zone}_{mms_id}') is False:
            return

        # Fetch all available filenames related to this record
        file_names = sorted([file_name for file_name in os.listdir(f'records/{zone}_{mms_id}')
                             if file_name.startswith(f'hol_{holding_id}') is True])

        if len(file_names) == 0:
            return

        return XmlData(filepath=f'records/{zone}_{mms_id}/{file_names[-1]}')
