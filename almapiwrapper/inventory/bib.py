"""This module allows getting information and changing Alma bib records"""

import abc
import logging
import os
from copy import deepcopy
from typing import Optional, ClassVar, Literal, Union, List

from lxml import etree

import almapiwrapper.inventory as inventory
from ..record import Record, check_error, XmlData


class Bib(Record, metaclass=abc.ABCMeta):
    """Abstract class representing a bibliographic record.

    This class groups common methods for `IzBib` and `NzBib`. Only these two classes should be instantiated directly.

    :param mms_id: MMS ID of the record (str)
    :param zone: Zone of the record (str)
    :param env: Environment of the entity: 'P' for production, 'S' for sandbox
    :param data: Optional :class:`almapiwrapper.record.XmlData` object, useful to force update a record from a backup

    :ivar mms_id: MMS ID of the record
    :ivar zone: Zone of the record
    :ivar env: Execution environment
    :ivar data: :ivar data: :class:`almapiwrapper.record.XmlData` object, used to force update a record from a backup
    :ivar error: True if the record encountered an error
    :ivar parser: XML parser used for parsing responses
    :ivar error_msg: stores the error message if an error occurred

    :cvar area: 'Bibs'
    :cvar format: 'xml'
    :cvar api_base_url_bibs: Base URL of the bibs API

    Example:
        >>> bib = IzBib(mms_id="990002239540108281", zone="ABN", env="P")
        >>> print(bib.mms_id)
        990002239540108281
    """

    api_base_url_bibs: ClassVar[str] = f'{Record.api_base_url}/bibs'
    area = 'Bibs'
    format = 'xml'

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

    def _fetch_data(self) -> Optional[XmlData]:
        """Fetch bibliographic data and store it in the "data" attribute as an Etree element

        :return: None or :class:`almapiwrapper.record.XmlData` object
        """
        r = self._api_call('get',
                           f'{self.api_base_url_bibs}/{self.mms_id}',
                           headers=self._get_headers())

        if r.ok:
            logging.info(f'{repr(self)}: bib data available')
            return XmlData(r.content)

        self._handle_error(r, 'unable to fetch bib data')
        return None

    @check_error
    def get_mms_id(self) -> str:
        """Fetch the MMS ID from controlfield 001

        Useful when fetching the bibliographic record with the NZ ID.

        :return: str with MMS ID of 001 controlfield

        .. note::
            If the record encountered an error, this
            method will be skipped.
        """
        return self.data.find('.//controlfield[@tag="001"]').text

    @check_error
    def sort_fields(self) -> 'Bib':
        """Sort all the fields and subfields of the record

        :return: Bib

        .. note::
            If the record encountered an error, this
            method will be skipped.
        """
        if self._data is not None:
            self._data.sort_fields()
        return self

    @check_error
    def update(self) -> 'Bib':
        """Update data

        On IzBib records this method is used to change local fields. On NzBib records, other fields can
        be changed.

        :return: :class:`almapiwrapper.inventory.Bib`

        .. note::
            If the record encountered an error, this
            method will be skipped.
        """
        r = self._api_call('put',
                           f'{self.api_base_url_bibs}/{self.mms_id}',
                           data=bytes(self),
                           headers=self._get_headers())

        if r.ok:
            self.data = XmlData(r.content)
            logging.info(f'{repr(self)}: bib data updated in {self.zone}')
        else:
            self._handle_error(r, 'unable to update bib data')

        return self

    @check_error
    def save(self) -> 'Bib':
        """Save a record in the 'records' folder

        Versioning is supported. A suffix is added to the file path.

        Example: records/NZ_991170519490005501/bib_991170519490005501_01.xml

        :return: :class:`almapiwrapper.inventory.Bib`

        .. note::
            If the record encountered an error, this
            method will be skipped.
        """
        filepath = f'records/{self.zone}_{self.mms_id}/bib_{self.mms_id}.xml'
        self._save_from_path(filepath)
        return self

    @check_error
    def add_fields(self, fields: Union[etree.Element, List[etree.Element]]) -> 'Bib':
        """add_fields(self, fields: Union[etree.Element, List[etree.Element]]) -> 'Bib'
        Add fields to the data of the current record

        :param fields: must be an etree element or a list of etree elements

        :return: :class:`almapiwrapper.inventory.Bib`

        .. note::
            If the record encountered an error, this
            method will be skipped.
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
        """Fetch the data of the described record

        :param mms_id: bib record mms_id
        :param zone: zone of the record

        :return: :class:`almapiwrapper.record.XmlData` or None
        """
        if not os.path.isdir(f'records/{zone}_{mms_id}'):
            return None

        # Fetch all available filenames related to this record
        file_names = sorted([file_name for file_name in os.listdir(f'records/{zone}_{mms_id}')
                             if file_name.startswith(f'bib_{mms_id}') is True])

        if len(file_names) == 0:
            return None

        return XmlData(filepath=f'records/{zone}_{mms_id}/{file_names[-1]}')


class IzBib(Bib):
    """Class representing bibliographic record of the IZ

    It inherits from Bib for common methods with NzBib.

    :ivar mms_id: record mms_id
    :ivar zone: zone of the record
    :ivar env: environment of the entity: 'P' for production and 'S' for sandbox
    :ivar data: :class:`almapiwrapper.record.XmlData` object, useful to force update a record from a backup
    :ivar error: True if the record encountered an error
    :ivar parser: XML parser used for parsing responses
    :ivar error_msg: stores the error message if an error occurred

    :cvar area: 'Bibs'
    :cvar format: 'xml'
    :cvar api_base_url_bibs: Base URL of the bibs API

    :param mms_id: MMS ID of the record (str)
    :param zone: Zone of the record (str)
    :param env: Environment of the entity: 'P' for production, 'S' for sandbox
    :param data: Optional :class:`almapiwrapper.record.XmlData` object, useful to force update a record from a backup
    :param create_bib: if this parameter is True and no MMS ID is provided, a new IZ bib record is created
    :param from_nz_mms_id: if this parameter is True the system assumes that the provided MMS ID is a network ID
        and fetch data from it
    :param copy_nz_rec: if this parameter is True, if no record exists in the IZ for the provided
        NZ ID, the CZ record is copied from NZ

    """

    def __init__(self,
                 mms_id: Optional[str] = None,
                 zone: Optional[str] = None,
                 env: Literal['P', 'S'] = 'P',
                 from_nz_mms_id: Optional[bool] = False,
                 copy_nz_rec: Optional[bool] = False,
                 data: Optional[Union['XmlData', etree.Element]] = None,
                 create_bib: Optional[bool] = False) -> None:
        """Constructor of an IZ bibliographic record
        """

        super().__init__(mms_id, zone, env, data)
        self._holdings = None
        if from_nz_mms_id:
            self.data = self._fetch_bib_data_from_nz_id(copy_nz_rec)
            self.mms_id = self.get_mms_id()

        # Create a new holding if 'create_holding' is True
        if self.mms_id is None and data is not None and create_bib is True:
            if data.__class__.__name__ == '_Element':
                data = XmlData(etree.tostring(data))
            self._create_bib(data)

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
        r = self._api_call('get', f'{self.api_base_url_bibs}',
                           params={'nz_mms_id': nz_mms_id},
                           headers=self._get_headers())

        if r.ok:
            # Data found in the IZ for the NZ MMS ID provided
            logging.info(f'NZ {nz_mms_id}: bib data available in {self.zone} -> {repr(self)}')
            return XmlData(r.content)

        else:
            # Data not found in the IZ for the NZ MMS ID provided
            if copy_nz_rec is False:
                self._handle_error(r, 'unable to fetch bib data from NZ id')
                return None
            else:
                # if 'copy_nz_rec' parameter is True, it will try to copy the record from the NZ
                logging.warning(f'NZ MMS_ID {self.mms_id}: no data available in {self.zone}')
                return self._copy_record_from_nz()

    def _copy_record_from_nz(self) -> Optional[XmlData]:
        """Copy NZ record to IZ. Loads the data in 'data' attribute.

        :return: None or :class:`almapiwrapper.record.XmlData`
        """
        nz_mms_id = self.mms_id

        r = self._api_call('post', f'{self.api_base_url_bibs}',
                           params={'from_nz_mms_id': nz_mms_id},
                           data='<bib/>',
                           headers=self._get_headers())

        if r.ok:
            logging.info(f'Record {repr(self)} copied from NZ record {nz_mms_id}')
            return XmlData(r.content)
        else:
            self._handle_error(r, 'unable to copy NZ record to IZ')
            return None

    def _create_bib(self, data: XmlData) -> None:
        """Create a new IZ bib record with API.

        :return: None

        :param data: :class:`almapiwrapper.record.XmlData` object
        """

        r = self._api_call('post',
                           f'{self.api_base_url_bibs}',
                           headers=self._get_headers(),
                           data=bytes(data))

        if r.ok:
            self.data = XmlData(r.content)
            self.mms_id = self.get_mms_id()
            logging.info(f'{repr(self)}: IZ bib record created')
        else:
            self._handle_error(r, f'unable to create IZ bib record')

    @check_error
    def get_nz_mms_id(self) -> Optional[str]:
        """get_nz_mms_id(self) -> Optional[str]
        Fetch the NZ MMS ID of the IZ bib record

        :return: string with NZ record MMS ID.

        .. note::
            If the record encountered an error, this
            method will be skipped.
        """
        nz_mms_id = self.data.find('.//linked_record_id[@type="NZ"]')
        if nz_mms_id is not None:
            logging.info(f'{repr(self)}: get NZ mms_id: {nz_mms_id.text}')
            return nz_mms_id.text

        logging.error(f'{repr(self)}: no NZ MMS ID available')
        return None

    @check_error
    def delete(self, force: bool = False) -> None:
        """Delete bibliographic record in the IZ

        To delete locally a record,
        it needs to be unlinked from the NZ and without holdings and items.

        :param force: when True delete also holdings and items

        :return: None

        .. note::
            If the record encountered an error, this
            method will be skipped.
        """
        # Unlink NZ and IZ record
        error_message = None

        r = self._api_call('post',
                           f'{self.api_base_url_bibs}/{self.mms_id}',
                           params={'op': 'unlink_from_nz'},
                           data='<bib/>',
                           headers=self._get_headers())

        # Manage case when record is not linked to NZ => try to unlink it and check error message.
        if not r.ok:
            try:
                xml = etree.fromstring(r.content, parser=self.parser)
                error_message = xml.find('.//{http://com/exlibris/urm/general/xmlbeans}errorMessage').text
            except etree.XMLSyntaxError:
                error_message = 'unknown error'

        # Delete record
        if r.ok is True or (error_message is not None and 'Record not linked to Network Zone' in error_message):
            if r.ok:
                logging.info(f'{repr(self)} unlinked from NZ')

            elif error_message is not None and 'Record not linked to Network Zone' in error_message:
                logging.warning(f'{repr(self)}: not linked to NZ')

            # Delete the record in the IZ
            # Delete all holdings and items if 'force' is True
            r = self._api_call('delete',
                               f'{self.api_base_url_bibs}/{self.mms_id}',
                               headers=self._get_headers(), params={'override': 'true' if force is True else 'false'})
            if r.ok:
                logging.info(f'{repr(self)} deleted')
                return None

        self._handle_error(r, 'unable to delete the record')
        return None

    @check_error
    def get_holdings(self) -> List['inventory.Holding']:
        """Get list of holdings and store it in '_holdings' attribute

        It avoids having to reload it.

        :return: list of :class:`almapiwrapper.inventory.Holding` objects

        .. note::
            If the record encountered an error, this
            method will be skipped.
        """
        # Check if holdings already fetched
        if self._holdings is not None:
            return self._holdings

        r = self._api_call('get',
                           f'{self.api_base_url_bibs}/{self.mms_id}/holdings',
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
    def delete_holdings(self, force: bool = False) -> None:
        """Delete all holdings of the record with items if 'force' is True.

        :param force: when True delete the items too.

        :return: None

        .. note::
            If the record encountered an error, this
            method will be skipped.
        """
        for holding in self.get_holdings():
            holding.delete(force=force)

    @check_error
    def get_local_fields(self) -> List[etree.Element]:
        """get_local_fields(self) -> List[etree.Element]
        Fetch the list of the local fields of the records

        It looks for subfield "9" and then get the parent.

        :return: list of etree.Element

        .. note::
            If the record encountered an error, this
            method will be skipped.
        """
        local_fields = [field.getparent() for field in
                        self.data.findall('.//record/datafield/subfield[@code="9"]')
                        if field.text.lower() == 'local']
        return local_fields


class NzBib(Bib):
    """Class representing a Network Zone (NZ) bibliographic record.

    This class inherits from `Bib` and provides methods specific to NZ records, while sharing common functionality with `IzBib`.

    :ivar mms_id: MMS ID of the record
    :ivar env: Environment of the entity ('P' for production, 'S' for sandbox)
    :ivar data: :class:`almapiwrapper.record.XmlData` object, used to force update a record from a backup
    :ivar error: True if the record encountered an error
    :ivar parser: XML parser used for parsing responses
    :ivar error_msg: stores the error message if an error occurred

    :cvar area: 'Bibs'
    :cvar format: 'xml'
    :cvar api_base_url_bibs: Base URL of the bibs API


    :param mms_id: MMS ID of the record (str)
    :param env: Environment of the entity: 'P' for production, 'S' for sandbox
    :param data: Optional :class:`almapiwrapper.record.XmlData` object, useful to force update a record from a backup
    :param create_bib: If True, creates a new bib record in the NZ

    Example:
        >>> nz_bib = NzBib(mms_id="991043825829705501", env="P")
        >>> print(nz_bib.mms_id)
        991043825829705501

    """

    def __init__(self, mms_id: Optional[str] = None,
                 env: Literal['P', 'S'] = 'P',
                 data: Optional[XmlData] = None,
                 create_bib: bool = False) -> None:
        """
        Construct a bibliographic record of the NZ
        """
        if data is not None:
            if data.__class__.__name__ == '_Element':
                data = XmlData(etree.tostring(data))

        super().__init__(mms_id, 'NZ', env, data)

        if create_bib:
            self._create_bib()

    def __repr__(self) -> str:
        """Get a string representation of the object. Useful for logs.

        :return: string
        """
        return f"{self.__class__.__name__}('{self.mms_id}', '{self.env}')"

    @check_error
    def delete(self, force: bool = False) -> None:
        """Delete bibliographic record in the IZ

        To delete locally a record,
        it needs to be unlinked from the NZ and without holdings and items.

        :param force: when True delete also holdings and items

        :return: None

        .. note::
            If the record encountered an error, this
            method will be skipped.
        """

        # Delete record
        r = self._api_call('delete',
                           f'{self.api_base_url_bibs}/{self.mms_id}',
                           params={'override': 'true' if force is True else 'false'},
                           headers=self._get_headers())

        if r.ok:
            logging.info(f'{repr(self)} deleted')
            return

        self._handle_error(r, 'unable to delete the NZ record')

    @check_error
    def _create_bib(self) -> None:
        """Create a new NZ bib record with API

        :return: None

        .. note::
            If the record encountered an error, this
            method will be skipped.
        """

        r = self._api_call('post',
                           f'{self.api_base_url_bibs}',
                           headers=self._get_headers(),
                           data=bytes(self))

        if r.ok:
            self.data = XmlData(r.content)
            self.mms_id = self.get_mms_id()
            logging.info(f'{repr(self)}: NZ bib record created')

        else:
            self._handle_error(r, f'unable to create NZ bib record')
