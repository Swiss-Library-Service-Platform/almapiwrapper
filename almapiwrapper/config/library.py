"""This module allow to create and manage sets in Alma"""
from typing import Literal, Optional, List, Dict, Union
import logging
from ..record import JsonData, Record, check_error
import requests


def fetch_libraries(zone: str,
                    env: Optional[Literal['P', 'S']] = 'P') -> List['Library']:
    """This function fetch the data describing the libraries.

    :param zone: institutional zone
    :param env: environment of the entity: 'P' for production and 'S' for sandbox

    :return: List of :class:`almapiwrapper.config.library.Library`
    """

    libraries = []

    r = requests.get(f'{Library.api_base_url}/conf/libraries',
                     headers=Record.build_headers(data_format='json', env=env,
                                                  zone=zone, rights='RW', area='Conf'))

    # Check result
    if r.ok is True and 'library' in r.json():
        libraries_list = JsonData(r.json())
        libraries = [Library(code=lib_data['code'], zone=zone, env=env, data=lib_data)
                     for lib_data in libraries_list.content['library']]
    elif r.ok is True:
        _handle_error(r, 'no libraries data available', zone, env)

    else:
        _handle_error(r, 'unable to fetch libraries data', zone, env)

    return libraries

def _handle_error(r: requests.models.Response, msg: str, zone: str, env: Literal['P', 'S']) -> None:
    """Set the record error attribute to True and write the logs about the error

    :param r: request response of the api
    :param msg: context message of the error
    :return: None
    """
    json_data = r.json()
    error_message = json_data['errorList']['error'][0]['errorMessage']

    logging.error(f'fetch_reminders({zone}, {env}) - {r.status_code}: '
                  f'{msg} / {error_message}')


class Library(Record):
    """Class representing a reminder
    """

    def __init__(self,
                 code: Optional[str] = None,
                 zone: Optional[str] = None,
                 env: Optional[Literal['P', 'S']] = 'P',
                 library_id: Optional[str] = None,
                 data: Optional[Union[Dict, JsonData]] = None) -> None:
        """Constructor of `Reminder`

        :param code: code of the library
        :param zone: zone of the library
        :param env: environment of the library: 'P' for production and 'S' for sandbox
        :param library_id: library id
        :param data: data of the library, :class:`almapiwrapper.record.JsonData` object
        """
        super().__init__(zone, env, data)
        self.area = 'Conf'
        self.format = 'json'
        self.library_id = library_id
        self.code = code
        self._locations = None
        self._desks = None
        self._open_hours = None

        if data is not None:
            if not isinstance(data, JsonData):
                data = JsonData(data)
            self.data = data


    def _fetch_data(self) -> Optional[JsonData]:
        """This method fetch the data describing the reminder.

        :return: :class:`almapiwrapper.record.JsonData` object
        """
        r = self._api_call('get',
                           f'{self.api_base_url}/conf/libraries/{self.code}',
                           headers=self._get_headers())
        if r.ok is True:
            logging.info(f'{repr(self)}: library data available')
            return JsonData(r.json())
        else:
            self._handle_error(r, 'unable to fetch library data')

    def __repr__(self) -> str:
        """Get a string representation of the object. Useful for logs.

        :return: string
        """
        return f"{self.__class__.__name__}('{self.code}', '{self.zone}', '{self.env}')"

    @check_error
    def _fetch_locations(self) -> List['Location']:
        """Return the list of locations

        :return: list of locations
        """
        r = self._api_call('get',
                           f'{self.api_base_url}/conf/libraries/{self.code}/locations',
                           headers=self._get_headers())
        if r.ok is True and 'location' in r.json():
            logging.info(f'{repr(self)}: locations data available')
            return [Location(library_code=self.code, zone=self.zone, env=self.env, data=location_data) for location_data in r.json()['location']]
        elif r.ok and 'location' not in r.json():
            logging.warning(f'{repr(self)}: no locations data available')
            return []
        else:
            self._handle_error(r, 'unable to fetch locations data')

    @property
    def locations(self) -> List['Location']:
        """Property to get the locations of the library

        :return: list of locations of the library
        """
        if self._locations is None:
            self._locations = self._fetch_locations()

        return self._locations


    @check_error
    def _fetch_desks(self) -> List['Desk']:
        """get_locations(self) -> List
        Return the list of locations

        :return: list of locations
        """
        r = self._api_call('get',
                           f'{self.api_base_url}/conf/libraries/{self.code}/circ-desks',
                           headers=self._get_headers())
        if r.ok is True and 'circ_desk' in r.json():
            logging.info(f'{repr(self)}: circulation desks data available')
            return [Desk(library_code=self.code, code=desk_data['code'], zone=self.zone, env=self.env) for desk_data in r.json()['circ_desk']]
        elif r.ok and 'circ_desk' not in r.json():
            logging.warning(f'{repr(self)}: no circulation desks data available')
            return []
        else:
            self._handle_error(r, 'unable to fetch circulation desks data')

    @property
    def desks(self) -> List['Desk']:
        """Property to get the desks of the library

        :return: list of desks of the library
        """
        if self._desks is None:
            self._desks = self._fetch_desks()

        return self._desks

    @property
    def open_hours(self) -> 'OpenHours':
        """open_hours(self) -> 'OpenHours'
        Get the open hours of the library

        :param library_code: code of the library
        :return: object :class:`almapiwrapper.library.OpenHours`
        """
        if self._open_hours is None:
            self._open_hours = OpenHours(self.zone, self.code, self.env)
        return self._open_hours

    @open_hours.setter
    def open_hours(self, open_hours: 'OpenHours') -> None:
        """open_hours(self, open_hours: 'OpenHours') -> None
        Set the open hours of the library

        :param open_hours: object :class:`almapiwrapper.library.OpenHours`
        :return: None
        """
        self._open_hours = open_hours


class Location(Record):
    """Class representing a location
    """

    def __init__(self,
                 zone: str,
                 library_code: str,
                 code: Optional[str] = None,
                 env: Optional[Literal['P', 'S']] = 'P',
                 data: Optional[Union[Dict, JsonData]] = None) -> None:
        """Constructor of `Location`

        :param code: code of the location
        :param zone: zone of the location
        :param env: environment of the location: 'P' for production and 'S' for sandbox
        :param data: data of the location, :class:`almapiwrapper.record.JsonData` object
        """
        super().__init__(zone, env, data)
        self.library_code = library_code
        self.area = 'Conf'
        self.format = 'json'
        self.code = code

        if data is not None:
            if not isinstance(data, JsonData):
                data = JsonData(data)
            self.code = data.content['code']
            self.data = data

    def __repr__(self) -> str:
        """Get a string representation of the object. Useful for logs.

        :return: string
        """
        return f"{self.__class__.__name__}('{self.zone}', '{self.library_code}', '{self.code}', '{self.env}')"


    def _fetch_data(self) -> Optional[JsonData]:
        """This method fetch the data describing the location.

        :return: :class:`almapiwrapper.record.JsonData` object
        """
        r = self._api_call('get',
                           f'{self.api_base_url}/conf/libraries/{self.library_code}/locations/{self.code}',
                           headers=self._get_headers())
        if r.ok is True:
            logging.info(f'{repr(self)}: location data available')
            return JsonData(r.json())
        else:
            self._handle_error(r, 'unable to fetch location data')

    @check_error
    def save(self) -> 'Location':
        """save() -> 'Location'
        Save a Location record in the 'records' folder

        When saved, a suffix is added to the file path with the version.
        Example: records/<IZ>_<library_code>/location_<IZ>_<library_code>_<location_code>_<version>.xml

        :return: object :class:`almapiwrapper.library.Location`
        """
        filepath = f'records/{self.zone}_{self.library_code}/location_{self.zone}_{self.library_code}_{self.code}.json'
        self._save_from_path(filepath)
        return self

    @check_error
    def update(self) -> 'Location':
        """update() -> Location
        Update the location
        """
        r = self._api_call('put',
                           f'{self.api_base_url}/conf/libraries/{self.library_code}/locations/{self.code}',
                           headers=self._get_headers(),
                           data=bytes(self))

        if r.ok:
            logging.info(f'{repr(self)}: location updated.')
        else:
            self._handle_error(r, 'failed to update location')

        return self

    @check_error
    def create(self) -> 'Location':
        """create() -> 'Location'
        Create a new location
        """
        r = self._api_call('post',
                           f'{self.api_base_url}/conf/libraries/{self.library_code}/locations',
                           headers=self._get_headers(),
                           data=bytes(self))

        if r.ok is True:
            logging.info(f'{repr(self)}: new location created')
        else:
            self._handle_error(r, 'unable to create new location')

        return self

    @check_error
    def delete(self) -> None:
        """create() -> None
        Delete a location
        """
        r = self._api_call('delete',
                           f'{self.api_base_url}/conf/libraries/{self.library_code}/locations/{self.code}',
                           headers=self._get_headers())

        if r.ok is True:
            logging.info(f'{repr(self)}: location deleted')
        else:
            self._handle_error(r, 'unable to create new location')

        return None

    @property
    def fulfillment_unit(self) -> str:
        """fulfillment_unit() -> str
        Get the fulfillment unit

        :return: string containing the fulfillment unit
        """
        return self.data['fulfillment_unit']['value']

    @fulfillment_unit.setter
    def fulfillment_unit(self, fulfillment_unit: str) -> None:
        """fulfillment_unit(self, fulfillment_unit: str) -> None
        Set the fulfillment unit

        :return: None
        """
        self.data['fulfillment_unit']['value'] = fulfillment_unit
        if 'desc' in self.data['fulfillment_unit']:
            del self.data['fulfillment_unit']['desc']


class OpenHours(Record):
    """Class representing list of open hours
    """
    def __init__(self,
                 zone: str,
                 library_code: Optional[str] = None,
                 env: Optional[Literal['P', 'S']] = 'P',
                 data: Optional[Union[Dict, JsonData]] = None) -> None:
        """Constructor of `OpenHours`

        :param zone: zone of the open hours
        :param library_code: code of the library
        :param env: environment of the open hours: 'P' for production and 'S' for sandbox
        :param data: data of the open hours, :class:`almapiwrapper.record.JsonData` object
        """

        super().__init__(zone, env, data)
        self.library_code = library_code
        self.area = 'Conf'
        self.format = 'json'

        if data is not None:
            if not isinstance(data, JsonData):
                data = JsonData(data)
            self.data = data

    def __repr__(self) -> str:
        """Get a string representation of the object. Useful for logs.

        :return: string
        """
        if self.library_code is not None:
            return f"{self.__class__.__name__}('{self.zone}', '{self.library_code}', '{self.env}')"
        else:
            return f"{self.__class__.__name__}('{self.zone}', '{self.env}')"

    def _fetch_data(self) -> Optional[JsonData]:
        """This method fetch the data describing the open hours.

        :return: :class:`almapiwrapper.record.JsonData` object
        """
        if self.library_code is not None:
            params = {'scope': self.library_code}
        else:
            params = {}
        r = self._api_call('get',
                           f'{self.api_base_url}/conf/open-hours',
                           params=params,
                           headers=self._get_headers())
        if r.ok is True:
            logging.info(f'{repr(self)}: open hours data available')
            return JsonData(r.json())
        else:
            self._handle_error(r, 'unable to fetch open hours data')

    @check_error
    def update(self) -> 'OpenHours':
        """update(self) -> 'OpenHours'
        Update the open hours

        :return: object :class:`almapiwrapper.library.OpenHours`
        """
        r = self._api_call('put',
                           f'{self.api_base_url}/conf/open-hours',
                           headers=self._get_headers(),
                           data=bytes(self))

        if r.ok:
            logging.info(f'{repr(self)}: open hours updated.')
        else:
            self._handle_error(r, 'failed to update open hours')

        return self

    @check_error
    def save(self) -> 'OpenHours':
        """save(self) -> 'OpenHours'
        Save a OpenHours record in the 'records' folder

        When saved, a suffix is added to the file path with the version.
        Example: records/<IZ>/open_hours_<IZ>_<version>.xml

        :return: object :class:`almapiwrapper.library.OpenHours`
        """
        if self.library_code is not None:
            filepath = f'records/{self.zone}/open_hours_{self.zone}_{self.library_code}.json'
        else:
            filepath = f'records/{self.zone}/open_hours_{self.zone}.json'
        self._save_from_path(filepath)
        return self


class Desk(Record):
    """Class representing a desk
    """
    def __init__(self,
                 zone: str,
                 library_code: Optional[str] = None,
                 code: Optional[str] = None,
                 env: Optional[Literal['P', 'S']] = 'P') -> None:
        """Constructor of `Desk`

        :param zone: zone of the desk
        :param library_code: code of the library
        :param code: code of the desk
        :param env: environment of the desk: 'P' for production and 'S' for sandbox
        """
        super().__init__(zone, env)
        self.library_code = library_code
        self.area = 'Conf'
        self.format = 'json'
        self.code = code

    def __repr__(self) -> str:
        """Get a string representation of the object. Useful for logs.

        :return: string
        """
        return f"{self.__class__.__name__}('{self.zone}', '{self.library_code}', '{self.code}', '{self.env}')"

    def _fetch_data(self) -> Optional[JsonData]:
        """This method fetch the data describing the desk.

        :return: :class:`almapiwrapper.record.JsonData` object
        """
        r = self._api_call('get',
                           f'{self.api_base_url}/conf/libraries/{self.library_code}/circ-desks/{self.code}',
                           headers=self._get_headers())
        if r.ok is True:
            logging.info(f'{repr(self)}: desk data available')
            return JsonData(r.json())
        else:
            self._handle_error(r, 'unable to fetch desk data')

    @check_error
    def get_locations(self):
        """get_locations(self) -> List[Location]
        Return the list of locations

        :return: list of locations
        """

        locations = [Location(self.zone, self.library_code, location['location_code'], self.env)
                     for location in self.data['location']]
        return locations

    @check_error
    def save(self) -> 'Desk':
        """save() -> 'Desk'
        Save a Desk record in the 'records' folder"""
        filepath = f'records/{self.zone}/desk_{self.zone}_{self.library_code}_{self.code}.json'
        self._save_from_path(filepath)
        return self
