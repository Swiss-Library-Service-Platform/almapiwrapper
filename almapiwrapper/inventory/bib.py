"""This module allows getting information and changing Alma bib records"""

from typing import Optional, ClassVar, Literal, Union, List
import abc
import logging
import requests
from ..record import Record, check_error, XmlData
from lxml import etree
from copy import deepcopy
import almapiwrapper.inventory as inventory
import os


class Bib(Record, metaclass=abc.ABCMeta):
    """Class representing bibliographic record

    This abstract class groups common methods to "IzBib" and
    "NzBib". Only these two classes should be instanced.

    :ivar mms_id: record mms_id
    :ivar zone: zone of the record
    :ivar env: environment of the entity: 'P' for production and 'S' for sandbox
    :ivar data: :class:`almapiwrapper.record.XmlData`
        object, useful to force update a record from a backup
    """

    api_base_url_bibs: ClassVar[str] = f'{Record.api_base_url}/bibs'

    def __init__(self,
                 mms_id: str,
                 zone: str,
                 env: Literal['P', 'S'] = 'P',
                 data: Optional[XmlData] = None) -> None:
        """Constructor for bib records

        Generic constructor for IZ and NZ bibliographic records. This method is called
        by the "IzBib" and "NzBib" classes to initialize the common elements.
        """
        super().__init__(zone, env, data)
        self.mms_id = mms_id
        self.area = 'Bibs'
        self.format = 'xml'

    def _fetch_data(self) -> Optional[XmlData]:
        """Fetch bibliographic data and store it in the "data" attribute as an Etree element

        :return: None or :class:`almapiwrapper.record.XmlData` object
        """
        r = requests.get(f'{self.api_base_url_bibs}/{self.mms_id}', headers=self._get_headers())

        if r.ok is True:
            logging.info(f'{repr(self)}: bib data available')
            return XmlData(r.content)
        else:
            self._handle_error(r, 'unable to fetch bib data')

    @check_error
    def get_mms_id(self) -> str:
        """get_mms_id(self) -> str
        Fetch the MMS ID in controlfield 001

        Useful when fetching the bibliographic record with the NZ ID.

        :return: string with MMS ID of 001 controlfield
        """
        return self.data.find('.//controlfield[@tag="001"]').text

    @check_error
    def sort_fields(self) -> 'Bib':
        """sort_fields(self) -> 'Bib'
        Sort all the fields and subfields of the record

        :return: Bib
        """
        if self._data is not None:
            self._data.sort_fields()
        return self

    @check_error
    def update(self) -> 'Bib':
        """update(self) -> 'Bib'
        Update data

        On BibIz records this method is used to change local fields. On BibNz records, other fields can
        be changed.

        :return: Bib
        """
        r = requests.put(f'{self.api_base_url_bibs}/{self.mms_id}',
                         data=bytes(self),
                         headers=self._get_headers())

        if r.ok is True:
            self.data = XmlData(r.content)
            logging.info(f'{repr(self)}: bib data updated in {self.zone}')
        else:
            print(r.text)
            self._handle_error(r, 'unable to update bib data')

        return self

    @check_error
    def save(self) -> 'Bib':
        """save(self) -> 'Bib'
        Save a record in the 'records' folder

        Versioning is supported. A suffix is added to the file path.

        Example: records/NZ_991170519490005501/bib_991170519490005501_01.xml

        :return: Bib
        """
        filepath = f'records/{self.zone}_{self.mms_id}/bib_{self.mms_id}.xml'
        self._save_from_path(filepath)
        return self

    @check_error
    def add_fields(self, fields: Union[etree.Element, List[etree.Element]]) -> 'Bib':
        """add_fields(self, fields: Union[etree.Element, List[etree.Element]]) -> 'Bib'
        Add fields to the data of the current record

        :param fields: must be an etree element or a list of etree elements
        :return: Bib
        """
        # If fields is only one etree element, then transform it to a list
        if type(fields) is not list:
            fields = [fields]
        record = self.data.find('.//record')

        if record is None:
            # No record found
            logging.error(f'{repr(self)}: adding fields failed, no record available in data attribute')
            self.error = True
            return self

        # Add the fields
        for field in fields:
            record.append(deepcopy(field))
        logging.info(f'{repr(self)}: {len(fields)} fields added to the record')

        # Sort fields
        _ = self.sort_fields()

        return self

    @staticmethod
    def get_data_from_disk(mms_id: str, zone: str) -> Optional[XmlData]:
        """get_data_from_disk(mms_id, holding_id, item_id, zone)
        Fetch the data of the described record

        :param mms_id: bib record mms_id
        :param zone: zone of the record

        :return: :class:`almapiwrapper.record.XmlData` or None
        """
        if os.path.isdir(f'records/{zone}_{mms_id}') is False:
            return

        # Fetch all available filenames related to this record
        file_names = sorted([file_name for file_name in os.listdir(f'records/{zone}_{mms_id}')
                             if file_name.startswith(f'bib_{mms_id}') is True])

        if len(file_names) == 0:
            return

        return XmlData(filepath=f'records/{zone}_{mms_id}/{file_names[-1]}')


class IzBib(Bib):
    """Class representing bibliographic record of the IZ

    It inherits from Bib for common methods with NzBib.

    :ivar mms_id: record mms_id
    :ivar zone: zone of the record
    :ivar env: environment of the entity: 'P' for production and 'S' for sandbox
    :ivar from_nz_mms_id: if this parameter is True the system assumes that the provided MMS ID is a network ID
        and fetch data from it
    :ivar copy_nz_rec: if this parameter is True, if no record exists in the IZ for the provided
        NZ ID, the CZ record is copied from NZ
    :ivar data: :class:`almapiwrapper.record.XmlData`
        object, useful to force update a record from a backup
    """
    def __init__(self, mms_id: str,
                 zone: str,
                 env: Literal['P', 'S'] = 'P',
                 from_nz_mms_id: Optional[bool] = False,
                 copy_nz_rec: Optional[bool] = False,
                 data: Optional[XmlData] = None):
        """Constructor of an IZ bibliographic record
        """

        super().__init__(mms_id, zone, env, data)
        self._holdings = None
        if from_nz_mms_id is True:
            self.data = self._fetch_bib_data_from_nz_id(copy_nz_rec)
            self.mms_id = self.get_mms_id()

    def __repr__(self) -> str:
        """Get a string representation of the object. Useful for logs.

        :return: string
        """
        return f"{self.__class__.__name__}('{self.mms_id}', '{self.zone}', '{self.env}')"

    def _fetch_bib_data_from_nz_id(self, copy_nz_rec: Optional[bool] = False) -> Optional[XmlData]:
        """Check if the record exists already in the destination IZ

        :param copy_nz_rec: when True the record is copied from the NZ if it didn't already exist in the IZ
        :return: None or :class:`almapiwrapper.record.XmlData`
        """
        nz_mms_id = self.mms_id

        # Fetch data from nz mms_id
        r = requests.get(f'{self.api_base_url_bibs}',
                         params={'nz_mms_id': nz_mms_id},
                         headers=self._get_headers())

        if r.ok is True:
            # Data found in the IZ for the NZ MMS ID provided
            logging.info(f'NZ {nz_mms_id}: bib data available in {self.zone} -> {repr(self)}')
            return XmlData(r.content)

        else:
            # Data not found in the IZ for the NZ MMS ID provided
            if copy_nz_rec is False:
                self._handle_error(r, 'unable to fetch bib data from NZ id')
            else:
                # if 'copy_nz_rec' parameter is True, it will try to copy the record from the NZ
                logging.warning(f'NZ MMS_ID {self.mms_id}: no data available in {self.zone}')
                return self._copy_record_from_nz()

    def _copy_record_from_nz(self) -> Optional[XmlData]:
        """Copy NZ record to IZ. Loads the data in 'data' attribute.
        :return: None
        """
        nz_mms_id = self.mms_id

        r = requests.post(f'{self.api_base_url_bibs}',
                          params={'from_nz_mms_id': nz_mms_id},
                          data='<bib/>',
                          headers=self._get_headers())

        if r.ok is True:
            logging.info(f'Record {repr(self)} copied from NZ record {nz_mms_id}')
            return XmlData(r.content)
        else:
            self._handle_error(r, 'unable to copy NZ record to IZ')

    @check_error
    def get_nz_mms_id(self) -> Optional[str]:
        """get_nz_mms_id(self) -> Optional[str]
        Fetch the NZ MMS ID of the IZ bib record

        :return: string with NZ record MMS ID.
        """
        nz_mms_id = self.data.find('.//linked_record_id[@type="NZ"]')
        if nz_mms_id is not None:
            logging.info(f'{repr(self)}: get NZ mms_id: {nz_mms_id.text}')
            return nz_mms_id.text

        logging.error(f'{repr(self)}: no NZ MMS ID available')
        return None

    @check_error
    def delete(self, force: Optional[bool] = False) -> None:
        """delete(force: Optional[bool] = False) -> None
        Delete bibliographic record in the IZ

        To delete locally a record,
        it needs to be unlinked from the NZ and without holdings and items.

        :param force: when True delete also holdings and items
        :return: None
        """

        if force is True:
            # Will delete also items and holdings
            self.delete_holdings(force=True)

        # Unlink NZ and IZ record
        r = requests.post(f'{self.api_base_url_bibs}/{self.mms_id}',
                          params={'op': 'unlink_from_nz'},
                          data='<bib/>',
                          headers=self._get_headers())

        # Delete record
        if r.ok is True:
            logging.info(f'{repr(self)} unlinked from NZ')

            r = requests.delete(f'{self.api_base_url_bibs}/{self.mms_id}',
                                headers=self._get_headers(), params={'override': 'true'})
            if r.ok is True:
                logging.info(f'{repr(self)} deleted')
                return

        self._handle_error(r, 'unable to delete the record')

    @check_error
    def get_holdings(self) -> List['inventory.Holding']:
        """get_holdings(self) -> List['inventory.Holding']
        Get list of holdings and store it in '_holdings' attribute

        It avoids having to reload it.

        :return: list of :class:`almapiwrapper.inventory.Holding` objects
        """
        # Check if holdings already fetched
        if self._holdings is not None:
            return self._holdings

        r = requests.get(f'{self.api_base_url_bibs}/{self.mms_id}/holdings',
                         headers=self._get_headers())
        root = etree.fromstring(r.content, parser=self.parser)
        holdings_data = root.findall('.//holding')

        # No holding available
        if len(holdings_data) == 0:
            logging.warning(f'{repr(self)}: no holding found')
            self._holdings = []
            return self._holdings

        # List of holdings found
        logging.info(f'{repr(self)}: {len(holdings_data)} holdings fetched')

        self._holdings = []
        for holding in holdings_data:
            holding_id = holding.find('holding_id').text
            self._holdings.append(inventory.Holding(bib=self, holding_id=holding_id))

        return self._holdings

    @check_error
    def delete_holdings(self, force: Optional[bool] = False) -> None:
        """delete_holdings(self, force: Optional[bool] = False) -> None
        Delete all holdings of the record with items if 'force' is True.

        :param force: when True delete the items too.
        :return: None
        """
        for holding in self.get_holdings():
            holding.delete(force=force)

    @check_error
    def get_local_fields(self) -> List[etree.Element]:
        """get_local_fields(self) -> List[etree.Element]
        Fetch the list of the local fields of the records

        It looks for subfield "9" and then get the parent.

        :return: list of etree.Element
        """
        local_fields = [field.getparent() for field in
                        self.data.findall('.//record/datafield/subfield[@code="9"]')
                        if field.text.lower() == 'local']
        return local_fields


class NzBib(Bib):
    """Class representing a NZ bibliographic record.

    It inherits from Bib for common methods with IzBib.

    :ivar mms_id: record mms_id
    :ivar env: environment of the entity: 'P' for production and 'S' for sandbox
    :ivar data: :class:`almapiwrapper.record.XmlData` object, useful to
        force update a record from a backup
    :ivar create_bib: bool, if True, create a new bib record in the NZ
    """
    def __init__(self, mms_id: Optional[str] = None,
                 env: Literal['P', 'S'] = 'P',
                 data: Optional[XmlData] = None,
                 create_bib: Optional[bool] = False) -> None:
        """
        Construct a bibliographic record of the NZ
        :param mms_id: record MMS ID
        :param env: environment of the entity: 'P' for production and 'S' for sandbox
        :param
        """
        if data is not None:
            if data.__class__.__name__ == '_Element':
                data = XmlData(etree.tostring(data))

        super().__init__(mms_id, 'NZ', env, data)

        if create_bib is True:
            self._create_bib()

    def __repr__(self) -> str:
        """Get a string representation of the object. Useful for logs.
        :return: string
        """
        return f"{self.__class__.__name__}('{self.mms_id}', '{self.env}')"

    @check_error
    def delete(self, force: Optional[bool] = False) -> None:
        """delete(self) -> None
        Delete bibliographic record in the IZ

        To delete locally a record,
        it needs to be unlinked from the NZ and without holdings and items.

        :param force: when True delete also holdings and items
        :return: None
        """

        # Delete record
        r = requests.delete(f'{self.api_base_url_bibs}/{self.mms_id}',
                            params={'override': 'true' if force is True else 'false'},
                            headers=self._get_headers())

        if r.ok is True:
            logging.info(f'{repr(self)} deleted')
            return

        self._handle_error(r, 'unable to delete the NZ record')

    @check_error
    def _create_bib(self) -> None:
        """Create a new NZ bib record with API.

        .. note::
            If the record encountered an error, this
            method will be skipped.
        """

        r = requests.post(f'{self.api_base_url_bibs}', headers=self._get_headers(), data=bytes(self))

        if r.ok is True:
            self.data = XmlData(r.content)
            self.mms_id = self.get_mms_id()
            logging.info(f'{repr(self)}: NZ bib record created')

        else:
            self._handle_error(r, f'unable to create NZ bib record')


def fetch_bib(q: str, zone=str, env: Literal['P', 'S'] = 'P') -> List[Union[IzBib, NzBib]]:
    """

    :param q:
    :param zone:
    :param env:
    :return:
    """
    r = requests.get(f'{Bib.api_base_url_bibs}',
                     params={'q': q},
                     headers=Record._build_headers(data_format='xml', area='Bibs', zone=zone, env=env))
    return r.text