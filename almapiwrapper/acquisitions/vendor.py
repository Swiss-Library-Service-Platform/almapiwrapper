from ..record import Record, check_error, JsonData
from typing import Optional, Literal,ClassVar, Union
import almapiwrapper.acquisitions as acquisitionslib
from lxml import etree
import pandas as pd
import logging

class Vendor(Record):
    """Class representing a Vendor

    :ivar vendor_code: initial value: code of the vendor
    :ivar zone: initial value: zone of the vendor
    :ivar env: initial value: environment of the entity: 'P' for production and 'S' for sandbox
    :ivar data: :class:`almapiwrapper.record.JsonData` with raw vendor data
    """

    api_base_url_vendors: ClassVar[str] = f'{Record.api_base_url}/acq/vendors'

    def __init__(self,
                 vendor_code: Optional[str] = None,
                 zone: Optional[str] = None,
                 env: Literal['P', 'S'] = 'P',
                 data: Optional[Union[dict, JsonData]] = None) -> None:
        """Constructor of Vendor Object
        """

        super().__init__(zone, env)
        self.area = 'Acquisitions'
        self.format = 'json'
        self.vendor_code = vendor_code
        if data is not None:
            self._data = data if type(data) is JsonData else JsonData(data)
        elif vendor_code is not None:
            pass
        else:
            self.error = True
            logging.error('Missing information to construct an Vendor')

    def __repr__(self) -> str:
        """Get a string representation of the object. Useful for logs.

        :return: str representing the object
        """
        return f"{self.__class__.__name__}('{self.vendor_code}', '{self.zone}', '{self.env}')"

    def _fetch_data(self) -> Optional[JsonData]:
        """Fetch the json data of the vendor

        :return: :class:`almapiwrapper.record.JsonData` if no error else None
        """

        r = self._api_call('get',
                     f'{self.api_base_url_vendors}/{self.vendor_code}',
                           headers=self._get_headers())
        if r.ok is True:
            # Parse data
            json_data = JsonData(r.json())
            logging.debug(f"{self.__class__.__name__} data fetched")

            return json_data
        else:
            self._handle_error(r, 'unable to fetch vendor data')

    @check_error
    def update(self) -> 'acquisitionslib.Vendor':
        """update(self) -> 'acquisitionslib.Vendor'
        Update the Vendor

        .. note::
            If the record encountered an error, this
            method will be skipped.

        :return: object :class:`almapiwrapper.acquisitions.Vendor`
        """

        r = self._api_call('put',
                           f'{self.api_base_url_vendors}/{self.vendor_code}',
                           headers=self._get_headers(),
                           data=bytes(self))

        if r.ok is True:
            self.data = JsonData(r.json())
            logging.info(f'{repr(self)}: Vendor data updated')
        else:
            self._handle_error(r, 'unable to update vendor data')

        return self

    @check_error
    def save(self) -> 'acquisitionslib.Vendor':
        """save(self) -> acquisitionslib.Vendor
        Save a PO Line record in the 'records' folder

        When saved, a suffix is added to the file path with the version.
        Example: records/vendors/vendor_<IZ>_<set_id>_<version>.xml

        :return: object :class:`almapiwrapper.acquisitions.Vendor`

        .. note::
            If the record encountered an error, this
            method will be skipped.
        """
        filepath = f'records/vendors/vendor_{self.zone}_{self.vendor_code}.json'
        self._save_from_path(filepath)
        return self

    @check_error
    def create(self):
        """create(self) -> acquisitionslib.Vendor
        Create a Vendor

        :note: The vendor code must be unique, same for the account_id of each account.

        :return: object :class:`almapiwrapper.acquisitions.Vendor`
        """
        r = self._api_call('post',
                           f'{self.api_base_url_vendors}',
                           headers=self._get_headers(),
                           data=bytes(self))

        if r.ok is True:
            self._data = JsonData(r.json())
            self.vendor_code = self.data['code']
            logging.info(f'{repr(self)}: Vendor created: {self.vendor_code}')
        else:
            self._handle_error(r, 'unable to create Vendor')

        return self

    @check_error
    def delete(self) -> None:
        """delete(self) -> None"""
        r = self._api_call('delete',
                           f'{self.api_base_url_vendors}/{self.vendor_code}',
                           headers=self._get_headers())
        if r.ok is True:
            logging.info(f'{repr(self)}: Vendor deleted: {self.vendor_code}')
        else:
            self._handle_error(r, 'unable to delete Vendor')
