"""This module allows to get and update information about collections"""

from typing import Optional, Literal, List, ClassVar, Union
import logging
from ..record import Record, check_error, JsonData
import almapiwrapper.inventory as inventory
import json

import os


class Collection(Record):
    """
    Class representing a collection object

    Collections can be in NZ and in IZ. They contain list of bibliographic records.

    :ivar zone: zone of the record
    :ivar env: environment of the entity: 'P' for production and 'S' for sandbox
    :ivar data: :class:`almapiwrapper.record.JsonData` object or dict,
    useful to force update a record from a backup
    """

    api_base_url_bibs: ClassVar[str] = f'{Record.api_base_url}/bibs'

    def __init__(self,
                 pid: str,
                 zone: str,
                 env: Optional[Literal['P', 'S']] = 'P') -> None:
        """
        Construct a Collection record.

        """
        self.pid = pid
        self._bibs = None
        self.error = False
        self.error_msg = None
        self._data = None
        self.area = 'Bibs'
        self.format = 'json'
        self.zone = zone
        self.env = env

    def __repr__(self) -> str:
        """Get a string representation of the object. Useful for logs.

        :return: string
        """
        return f"{self.__class__.__name__}('{self.pid}', '{self.zone}', '{self.env}')"

    def _fetch_data(self) -> Optional[JsonData]:
        """Fetch holding data via API. Store the data in the 'data' attribute.

        :return: None
        """
        r = self._api_call('get',
                           f'{self.api_base_url_bibs}/collections/{self.pid}',
                           headers=self._get_headers())

        if r.ok is True:
            logging.info(f'{repr(self)}: collection data available')
            return JsonData(r.json())
        else:
            self._handle_error(r, 'unable to fetch collection data')



    @check_error
    def save(self) -> 'Collection':
        """save(self) -> 'Collection'
        Save collection in a folder.
        Example: records/UBS_9963486250105504/hol_22314215780005504_01.xml

        :return: Collection
        """
        filepath = f'records/{self.zone}_collections/hol_{self.pid}.xml'
        self._save_from_path(filepath)
        return self

    # @check_error
    # def update(self) -> 'Holding':
    #     """update(self) -> 'Holding'
    #     Update data of a holding.
    #
    #     :return: Holding
    #     """
    #     r = self._api_call('put',
    #                        f'{self.api_base_url_bibs}/{self.bib.mms_id}/holdings/{self.holding_id}',
    #                        data=etree.tostring(self.data),
    #                        headers=self._get_headers())
    #
    #     if r.ok is True:
    #         self.data = XmlData(r.content)
    #         logging.info(f'{repr(self)}: holding data updated')
    #     else:
    #         self._handle_error(r, 'unable to update holding data')
    #
    #     return self
    #
    # @check_error
    # def delete(self, force: Optional[bool] = False) -> None:
    #     """delete(self, force: Optional[bool] = False) -> None
    #     Delete holding
    #
    #     :return: None
    #     """
    #     if force is True:
    #         self.delete_items()
    #
    #     r = self._api_call('delete',
    #                        f'{self.api_base_url_bibs}/{self.bib.mms_id}/holdings/{self.holding_id}',
    #                        headers=self._get_headers())
    #     if r.ok is True:
    #         logging.info(f'{repr(self)} deleted')
    #     else:
    #         self._handle_error(r, 'unable to delete the holding')
    #
    # @check_error
    # def get_items(self) -> List['inventory.Item']:
    #     """get_items(self) -> List['inventory.Item']
    #     This method is used to retrieve the list of items and loads
    #     the xml data of these items. To avoid reloading this information,
    #     the items references are stored in the private attribute '_items'.
    #
    #     :return: list of :class:`almapiwrapper.bib.Item` objects
    #     """
    #     # Check if items have been already fetched
    #     if self._items is not None:
    #         return self._items
    #
    #     # Fetch the item's data through apis
    #     r = self._api_call('get',
    #                        f'{self.api_base_url_bibs}/{self.bib.mms_id}/holdings/{self.holding_id}/items',
    #                        params={'limit': '100'},
    #                        headers=self._get_headers())
    #
    #     if r.ok is True:
    #         root = etree.fromstring(r.content, parser=self.parser)
    #     else:
    #         self._handle_error(r, 'unable to fetch items')
    #         return []
    #
    #     items_data = root.findall('.//item_data')
    #     if len(items_data) > 99:
    #         logging.warning(f'{repr(self)}: at least 100 items, risk of missing items')
    #
    #     # No item found
    #     if len(items_data) == 0:
    #         logging.warning(f'{repr(self)}: no item found')
    #         self._items = []
    #         return self._items
    #
    #     logging.info(f'{repr(self)}: {len(items_data)} items fetched')
    #
    #     # Fetch items one by one
    #     self._items = []
    #     for item in items_data:
    #         item_id = item.find('.//pid').text
    #         self._items.append(inventory.Item(holding=self, item_id=item_id))
    #
    #     return self._items
    #
    # @check_error
    # def delete_items(self) -> None:
    #     """delete_items(self) -> None
    #     Delete all items of the holding
    #
    #     :return: None
    #     """
    #     for item in self.get_items():
    #         item.delete()
    #
    # @property

    def _fetch_bibs(self):
        """Fetch bibs of the collection via API. Store the data in the 'bibs' attribute.

        :return: None
        """

        self._bibs = []
        rec_count = None
        mms_ids = []
        while rec_count is None or len(mms_ids) < rec_count:
            r = self._api_call('get',
                               f'{self.api_base_url_bibs}/collections/{self.pid}/bibs',
                               params={'limit': '100', 'offset': str(len(mms_ids))},
                               headers=self._get_headers())
            if r.ok is False:
                self._handle_error(r, f'{repr(self)}: unable to fetch set members')
                return
            data = r.json()
            rec_count = data['total_record_count']
            if 'bib' in data:
                mms_ids += [rec['mms_id'] for rec in data['bib']]
                logging.info(f'{repr(self)}: {len(mms_ids)} / {rec_count} records fetched')
        if self.zone != 'NZ':
            self._bibs = [inventory.IzBib(mms_id, self.zone, self.env) for mms_id in mms_ids]
        else:
            self._bibs = [inventory.NzBib(mms_id, self.env) for mms_id in mms_ids]


    @property
    @check_error
    def bibs(self) -> Optional[List]:
        """bibs(self) -> Optional[List]
        Property of the collection returning the list containing bib records

        :return: List containing bib records
        """
        if self._bibs is None:
            self._fetch_bibs()

        return self._bibs

    def add_bib(self, bib: Union[inventory.IzBib, inventory.NzBib, str]) -> None:
        """add_bib(self, bib: Union[inventory.IzBib, inventory.NzBib]) -> None
        Add a bib to the collection

        :param bib: bib to add to the collection

        :return: None
        """

        if isinstance(bib, inventory.IzBib) or isinstance(bib, inventory.NzBib):
            mms_id = bib.mms_id
        else:
            mms_id = bib
        xml = f'<bib><mms_id>{mms_id}</mms_id></bib>'
        # jsondata = {'bib':[{'mms_id': mms_id}] }
        r = self._api_call('post',
                            f'{self.api_base_url_bibs}/collections/{self.pid}/bibs',
                            data=xml,
                            headers=self._get_headers(data_format='xml'))

        if r.ok is False:
            self._handle_error(r, f'{repr(self)}: unable to add bib {mms_id} to collection')
            return
        self._bibs = None
        logging.info(f'{repr(self)}: bib {mms_id} added to collection')

    def remove_bib(self, bib: Union[inventory.IzBib, inventory.NzBib, str]) -> None:
        """remove_bib(self, bib: Union[inventory.IzBib, inventory.NzBib]) -> None
        Remove a bib from the collection

        :param bib: bib to remove from the collection

        :return: None
        """

        if isinstance(bib, inventory.IzBib) or isinstance(bib, inventory.NzBib):
            mms_id = bib.mms_id
        else:
            mms_id = bib

        r = self._api_call('delete',
                            f'{self.api_base_url_bibs}/collections/{self.pid}/bibs/{mms_id}',
                            headers=self._get_headers())

        if r.ok is False:
            self._handle_error(r, f'{repr(self)}: unable to remove bib {mms_id} from collection')
            return
        self._bibs = None
        logging.info(f'{repr(self)}: bib {mms_id} removed from collection')



    # @library.setter
    # @check_error
    # def library(self, library_code: str) -> None:
    #     """library(self, library_code: str) -> None
    #     This setter is able to update the 852$b of the holding. But the field should already exist.
    #
    #     :param library_code: code of the library to insert in 852$b field
    #
    #     :return: None
    #     """
    #     library = self.data.find('.//datafield[@tag="852"]/subfield[@code="b"]')
    #     if library is None:
    #         logging.error(f'{repr(self)}: no library field in the holding -> not possible to update it')
    #         self.error = True
    #     else:
    #         logging.info(f'{repr(self)}: library changed from "{library.text}" to "{library_code}"')
    #         library.text = library_code
    #
    # @property
    # @check_error
    # def location(self) -> Optional[str]:
    #     """location(self) -> Optional[str]
    #     Property of the holding returning the library code
    #
    #     :return: str containing library code
    #     """
    #     location = self.data.find('.//datafield[@tag="852"]/subfield[@code="c"]')
    #     if location is None:
    #         logging.warning(f'{repr(self)}: no location in the holding')
    #         return
    #     return location.text
    #
    # @location.setter
    # @check_error
    # def location(self, location_code: str) -> None:
    #     """location(self, location_code: str) -> None
    #     This setter is able to update the 852$c of the holding. But the field should already exist.
    #
    #     :param location_code: location code to set to the holding
    #
    #     :return: None
    #     """
    #     location = self.data.find('.//datafield[@tag="852"]/subfield[@code="c"]')
    #     if location is None:
    #         logging.error(f'{repr(self)}: no location field in the holding -> not possible to update it')
    #     else:
    #         logging.info(f'{repr(self)}: location changed from "{location.text}" to "{location_code}"')
    #         location.text = location_code
    #
    # @property
    # @check_error
    # def callnumber(self) -> Optional[str]:
    #     """callnumber(self) -> Optional[str]
    #     Property of the holding returning the callnumber
    #
    #     :return: str containing callnumber
    #     """
    #     field852 = self.data.find('.//datafield[@tag="852"]')
    #     if field852 is None:
    #         return None
    #
    #     callnumber_field = field852.find('./subfield[@code="j"]')
    #
    #     if callnumber_field is None:
    #         callnumber_field = field852.find('./subfield[@code="h"]')
    #
    #     if callnumber_field is None:
    #         logging.warning(f'{repr(self)}: no callnumber field in the holding')
    #         return None
    #
    #     return callnumber_field.text
    #
    # @callnumber.setter
    # @check_error
    # def callnumber(self, callnumber_txt: str) -> None:
    #     """callnumber(self, callnumber_txt: str) -> None
    #     This setter is able to update the 852$j or 852$h of the holding. But the field should already exist.
    #
    #     :param callnumber_txt: text of the callnumber to be set in j or h subfield
    #
    #     :return: None
    #     """
    #     field852 = self.data.find('.//datafield[@tag="852"]')
    #     if field852 is None:
    #         return
    #
    #     callnumber_field = field852.find('./subfield[@code="j"]')
    #
    #     if callnumber_field is None:
    #         callnumber_field = field852.find('./subfield[@code="h"]')
    #
    #     if callnumber_field is None:
    #         logging.error(f'{repr(self)}: no callnumber field in the holding -> not possible to update it')
    #         return
    #
    #     logging.info(f'{repr(self)}: callnumber changed from "{callnumber_field.text}" to "{callnumber_txt}"')
    #     callnumber_field.text = callnumber_txt
    #
    # @staticmethod
    # def get_data_from_disk(mms_id: str, holding_id: str, zone: str) -> Optional[XmlData]:
    #     """get_data_from_disk(mms_id, holding_id, zone)
    #     Fetch the data of the described record
    #
    #     :param mms_id: bib record mms_id
    #     :param holding_id: holding record ID
    #     :param zone: zone of the record
    #
    #     :return: :class:`almapiwrapper.record.XmlData` or None
    #     """
    #     if os.path.isdir(f'records/{zone}_{mms_id}') is False:
    #         return
    #
    #     # Fetch all available filenames related to this record
    #     file_names = sorted([file_name for file_name in os.listdir(f'records/{zone}_{mms_id}')
    #                          if file_name.startswith(f'hol_{holding_id}') is True])
    #
    #     if len(file_names) == 0:
    #         return
    #
    #     return XmlData(filepath=f'records/{zone}_{mms_id}/{file_names[-1]}')
