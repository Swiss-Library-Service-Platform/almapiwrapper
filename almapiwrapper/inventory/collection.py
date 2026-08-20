"""This module allows to get and update information about collections"""

from typing import Optional, Literal, List, ClassVar, Union, Dict
import logging
from almapiwrapper.record import Record, check_error, JsonData
import almapiwrapper.inventory as inventory


def _handle_error(r, msg: str, zone: str, env: Optional[Literal['P', 'S']] = 'P') -> None:
    """Log errors for top-level collection fetch functions."""
    try:
        json_data = r.json()
        error_message = json_data['errorList']['error'][0]['errorMessage']
    except Exception:
        error_message = r.text if r is not None and hasattr(r, 'text') else 'unknown error'

    status_code = r.status_code if r is not None and hasattr(r, 'status_code') else 'unknown'
    logging.error(f'fetch_collections({zone}, {env}) - {status_code}: {msg} / {error_message}')


def fetch_collections(zone: str,
                     env: Literal['P', 'S'] = 'P',
                     level: Optional[int] = 1,
                     q: Optional[str] = None) -> List['Collection']:
    """Fetch a list of collections from Alma

    :param level: level of the collection, 1 for top-level collections, 2 for sub-collections
    :param q: query to filter collections, for example 'name~"test"'
    :param zone: zone of the record
    :param env: environment of the entity: 'P' for production and 'S' for sandbox

    :return: list of :class:`almapiwrapper.inventory.Collection` objects
    """
    if level is not None and level < 1:
        raise ValueError('level must be >= 1')

    # Alma API does not support using both query and level together.
    if level is not None and q is not None:
        raise ValueError('Parameters "level" and "q" cannot be used together')

    params = {}
    if level is not None:
        params['level'] = str(level)
    if q is not None:
        params['q'] = q

    collections = []
    r = Record.api_call('get',
                        f'{Record.api_base_url}/bibs/collections',
                        params=params,
                        headers=Record.build_headers(data_format='json', env=env,
                                                     zone=zone, rights='RW', area='Bibs'))

    if r is None or not r.ok:
        _handle_error(r, 'unable to fetch collections data', zone, env)
        return collections

    collections_list = r.json()

    def get_collections(collections, data):
        if 'collection' in data:
            for col_data in data['collection']:
                pid = col_data.get('pid')
                if isinstance(pid, dict):
                    pid = pid.get('value')
                if pid is None:
                    logging.warning(f'fetch_collections("{zone}", "{env}"): collection without pid skipped')
                    continue
                collection = {'collection': Collection(str(pid), zone, env), 'children': []}
                collections.append(collection)
                if 'collection' in col_data:
                    get_collections(collection['children'], col_data)
        return None


    total_record_count = collections_list.get('total_record_count', 0)
    collections = []
    get_collections(collections, collections_list)

    logging.info(f'fetch_collections("{zone}", "{env}", level={level}, q="{q}"): '
                 f'{len(collections)} / {total_record_count} collections data available')
    return collections


class Collection(Record):
    """Class representing a collection object

    Collections can be in NZ and in IZ. They contain list of bibliographic records.

    :ivar zone: zone of the record
    :ivar env: environment of the entity: 'P' for production and 'S' for sandbox
    :ivar data: :class:`almapiwrapper.record.JsonData` object or dict, useful to force update a record from a backup
    :ivar error: boolean indicating if an error occurred during the last operation
    :ivar error_msg: string containing the error message if an error occurred during the last operation
    :ivar pid: collection ID

    :cvar api_base_url_bibs: base URL for bibs API calls
    :cvar area: area of the API
    :cvar format: format of the data json for collections


    :param pid: collection ID
    :param zone: zone of the record
    :param env: environment of the entity: 'P' for production and 'S' for sandbox

    """
    api_base_url_bibs: ClassVar[str] = f'{Record.api_base_url}/bibs'
    area = 'Bibs'
    format = 'json'

    def __init__(self,
                 pid: Optional[str] = None,
                 zone: str = None,
                 env: Literal['P', 'S'] = 'P',
                 data: Optional[Dict] = None) -> None:
        """Construct a Collection record
        """
        super().__init__(zone, env, data)
        self.pid = pid
        self._bibs = None

    def __repr__(self) -> str:
        """Get a string representation of the object. Useful for logs.

        :return: string
        """
        return f"{self.__class__.__name__}('{self.pid}', '{self.zone}', '{self.env}')"

    def _fetch_data(self) -> Optional[JsonData]:
        """Fetch collection data via API. Store the data in the 'data' attribute.

        :return: JsonData object containing the data of the collection or None if an error occurred
        """
        if self.pid is None:
            self.error = True
            self.error_msg = 'Collection ID is required to fetch collection data'
            logging.error(f'{repr(self)}: collection ID is required to fetch collection data')
            return None

        r = self.api_call('get',
                           f'{self.api_base_url_bibs}/collections/{self.pid}',
                          headers=self._get_headers())

        if r.ok:
            logging.info(f'{repr(self)}: collection data available')
            return JsonData(r.json())
        else:
            self._handle_error(r, 'unable to fetch collection data')
            return None

    @check_error
    def create(self) -> 'Collection':
        """Create a new collection in Alma from ``self.data``.

        :return: :class:`almapiwrapper.inventory.Collection` object
        """
        if self.data is None:
            self.error = True
            self.error_msg = 'Collection data is required to create a collection'
            logging.error(f'{repr(self)}: collection data is required to create a collection')
            return self

        r = self.api_call('post',
                          f'{self.api_base_url_bibs}/collections',
                          data=bytes(self),
                          headers=self._get_headers())

        if r.ok:
            self.data = JsonData(r.json())
            pid = self.data.get('pid')
            if isinstance(pid, dict):
                pid = pid.get('value')
            if pid is not None:
                self.pid = str(pid)
            logging.info(f'{repr(self)}: collection created')
        else:
            self._handle_error(r, 'unable to create collection')

        return self

    @check_error
    def update(self) -> 'Collection':
        """Update an existing collection in Alma.

        :return: :class:`almapiwrapper.inventory.Collection` object
        """
        if self.pid is None:
            self.error = True
            self.error_msg = 'Collection ID is required to update a collection'
            logging.error(f'{repr(self)}: collection ID is required to update a collection')
            return self

        if self.data is None:
            self.error = True
            self.error_msg = 'Collection data is required to update a collection'
            logging.error(f'{repr(self)}: collection data is required to update a collection')
            return self

        r = self.api_call('put',
                          f'{self.api_base_url_bibs}/collections/{self.pid}',
                          data=bytes(self),
                          headers=self._get_headers())

        if r.ok:
            self.data = JsonData(r.json())
            logging.info(f'{repr(self)}: collection updated')
        else:
            self._handle_error(r, 'unable to update collection')

        return self

    @check_error
    def delete(self) -> None:
        """Delete a collection in Alma.

        :return: None
        """
        if self.pid is None:
            self.error = True
            self.error_msg = 'Collection ID is required to delete a collection'
            logging.error(f'{repr(self)}: collection ID is required to delete a collection')
            return None

        r = self.api_call('delete',
                          f'{self.api_base_url_bibs}/collections/{self.pid}',
                          headers=self._get_headers())

        if r.ok:
            logging.info(f'{repr(self)}: collection deleted')
            return None

        self._handle_error(r, 'unable to delete collection')
        return None



    @check_error
    def save(self) -> 'Collection':
        """Save collection in a folder.

        Example: records/UBS_9963486250105504/hol_22314215780005504_01.xml

        :return: :class:`almapiwrapper.inventory.Collection` object
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
            r = self.api_call('get',
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
    def bibs(self) -> Optional[List[Union[inventory.IzBib, inventory.NzBib]]]:
        """Property of the collection returning the list containing bib records

        :return: List containing :class:`almapiwrapper.inventory.IzBib`
            objects or :class:`almapiwrapper.inventory.NzBib` objects
        """
        if self._bibs is None:
            self._fetch_bibs()

        return self._bibs

    def add_bib(self, bib: Union[inventory.IzBib, inventory.NzBib, str]) -> None:
        """Add a bib to the collection

        :param bib: :class:`almapiwrapper.inventory.IzBib` or :class:`almapiwrapper.inventory.NzBib` to add to the collection

        :return: None
        """

        if isinstance(bib, inventory.IzBib) or isinstance(bib, inventory.NzBib):
            mms_id = bib.mms_id
        else:
            mms_id = bib
        xml = f'<bib><mms_id>{mms_id}</mms_id></bib>'

        r = self.api_call('post',
                            f'{self.api_base_url_bibs}/collections/{self.pid}/bibs',
                          data=xml,
                          headers=self._get_headers(data_format='xml'))

        if not r.ok:
            self._handle_error(r, f'{repr(self)}: unable to add bib {mms_id} to collection')
            return
        self._bibs = None

        logging.info(f'{repr(self)}: bib {mms_id} added to collection')

    def remove_bib(self, bib: Union[inventory.IzBib, inventory.NzBib, str]) -> None:
        """Remove a bib from the collection

        :param bib: :class:`almapiwrapper.inventory.IzBib` or :class:`almapiwrapper.inventory.NzBib` to remove
            from the collection, can be either a NZ or an IZ bib or a mms_id

        :return: None
        """

        if isinstance(bib, inventory.IzBib) or isinstance(bib, inventory.NzBib):
            mms_id = bib.mms_id
        else:
            mms_id = bib

        r = self.api_call('delete',
                            f'{self.api_base_url_bibs}/collections/{self.pid}/bibs/{mms_id}',
                          headers=self._get_headers())

        if not r.ok:
            self._handle_error(r, f'{repr(self)}: unable to remove bib {mms_id} from collection')
            return
        self._bibs = None
        logging.info(f'{repr(self)}: bib {mms_id} removed from collection')
