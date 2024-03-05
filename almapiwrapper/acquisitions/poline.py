from ..record import Record, check_error, JsonData
from ..inventory import Item
from typing import Optional, Literal,ClassVar, Union, List
import almapiwrapper.acquisitions as acquisitionslib
from lxml import etree
import pandas as pd
import logging

class POLine(Record):
    """Class representing a POLine

    """

    api_base_url_acquisitions: ClassVar[str] = f'{Record.api_base_url}/acq/po-lines'

    def __init__(self,
                 pol_number: Optional[str] = None,
                 zone: Optional[str] = None,
                 env: Literal['P', 'S'] = 'P',
                 data: Optional[Union[dict, JsonData]] = None) -> None:
        """Constructor of POLine Object
        """

        super().__init__(zone, env)
        self.area = 'Acquisitions'
        self.format = 'json'
        self.pol_number = pol_number
        if data is not None:
            self._data = data if type(data) is JsonData else JsonData(data)
        elif pol_number is not None:
            pass
        else:
            self.error = True
            logging.error('Missing information to construct an POLine')

    def __repr__(self) -> str:
        """Get a string representation of the object. Useful for logs.
        :return: str
        """
        return f"{self.__class__.__name__}('{self.pol_number}', '{self.zone}', '{self.env}')"

    def _fetch_data(self) -> Optional[JsonData]:
        """Fetch the json data of the POLine

        :return: :class:`almapiwrapper.record.JsonData` if no error else None
        """

        r = self._api_call('get',
                     f'{self.api_base_url_acquisitions}/{self.pol_number}',
                           headers=self._get_headers())
        if r.ok is True:
            # Parse data
            json_data = JsonData(r.json())
            logging.debug(f"{self.__class__.__name__} data fetched")

            return json_data
        else:
            self._handle_error(r, 'unable to fetch POLine data')

    @check_error
    def update(self) -> 'acquisitionslib.POLine':
        """Update the POLine

        :return: POLine object
        """

        r = self._api_call('put',
                           f'{self.api_base_url_acquisitions}/{self.pol_number}',
                           headers=self._get_headers(),
                           data=bytes(self))

        if r.ok is True:
            self.data = JsonData(r.json())
            logging.info(f'{repr(self)}: POLine data updated')
        else:
            self._handle_error(r, 'unable to update POLine data')

        return self

    @check_error
    def save(self) -> 'acquisitionslib.POLine':
        """save(self) -> acquisitionslib.POLine
        Save a PO Line record in the 'records' folder

        When saved, a suffix is added to the file path with the version.
        Example: records/polines/pol_<IZ>_<set_id>_<version>.xml

        :return: object :class:`almapiwrapper.acquisitions.POLine`

        .. note::
            If the record encountered an error, this
            method will be skipped.
        """
        filepath = f'records/polines/pol_{self.zone}_{self.pol_number}.json'
        self._save_from_path(filepath)
        return self

    @check_error
    def create(self):
        r = self._api_call('post',
                           f'{self.api_base_url_acquisitions}',
                           headers=self._get_headers(),
                           data=bytes(self))

        if r.ok is True:
            print(r.text)
            self._data = JsonData(r.json())
            self.pol_number = self.data['number']
            logging.info(f'{repr(self)}: POLine data created: {self.pol_number}')
        else:
            self._handle_error(r, 'unable to create POLine')

        return self

    @check_error
    def get_items(self) -> List[Item]:
        """Get the items of the POLine

        :return: list of :class:`almapiwrapper.inventory.Item`
        """
        items = []
        for location in self.data['location']:
            for item in location['copy']:
                items.append(Item(barcode=item['barcode'],
                                  zone=self.zone,
                                  env=self.env))
        return items

    @check_error
    def get_vendor(self) -> Optional['acquisitionslib.Vendor']:
        """Get the vendor of the POLine

        :return: :class:`almapiwrapper.acquisitions.Vendor` or None if not available
        """
        if 'vendor' in self.data and 'value' in self.data['vendor']:
            return acquisitionslib.Vendor(vendor_code=self.data['vendor']['value'],
                                          zone=self.zone,
                                          env=self.env)
        else:
            return None

    @check_error
    def receive_item(self, item: Item, receive_date: Optional[str] = None) -> 'acquisitionslib.POLine':
        """Receive an item of the POLine

        :param item: :class:`almapiwrapper.inventory.Item`
        :param receive_date: str : date of the reception in format YYYY-MM-DDZ

        :return: POLine object
        """
        if item.error is True:
            logging.error(f'{repr(self)}: unable to receive item {repr(item)}, item has an error')
            return self
        params = {'op': 'receive'}
        if receive_date is not None:
            params['receive_date'] = receive_date
        headers = self._get_headers()
        headers['content-type'] = 'application/xml'

        r = self._api_call('post',
                           f'{self.api_base_url_acquisitions}/{self.pol_number}/items/{item.item_id}',
                           params=params,
                           headers=headers,
                           data=bytes(item))

        if r.ok is True:
            logging.info(f'{repr(self)}: Item {repr(item)} received.')
        else:
            self._handle_error(r, 'unable to receive item')

        return self
