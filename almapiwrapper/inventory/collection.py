"""This module allows to get and update information about collections"""

from typing import Optional, Literal, List, ClassVar, Union
import logging
from ..record import Record, check_error, JsonData
import almapiwrapper.inventory as inventory


class Collection(Record):
    """
    Class representing a collection object

    Collections can be in NZ and in IZ. They contain list of bibliographic records.

    :ivar zone: zone of the record
    :ivar env: environment of the entity: 'P' for production and 'S' for sandbox
    :ivar data: :class:`almapiwrapper.record.JsonData` object or dict, useful to force update a record from a backup
    :ivar error: boolean indicating if an error occurred during the last operation
    :ivar error_msg: string containing the error message if an error occurred during the last operation
    :ivar pid: collection ID

    """

    api_base_url_bibs: ClassVar[str] = f'{Record.api_base_url}/bibs'

    def __init__(self,
                 pid: str,
                 zone: str,
                 env: Optional[Literal['P', 'S']] = 'P') -> None:
        """Construct a Collection record

        :param pid: collection ID
        :param zone: zone of the record
        :param env: environment of the entity: 'P' for production and 'S' for sandbox

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

    def _fetch_bibs(self):
        """Fetch bibs of the collection via API. Store the data in the 'bibs' attribute.

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

        :param bib: bib to remove from the collection, can be either a NZ
            or an IZ bib or a mms_id

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
