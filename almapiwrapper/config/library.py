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
    #
    # @check_error
    # def save(self) -> 'Reminder':
    #     """save() -> 'Reminder'
    #     Save a Reminder record in the 'records' folder
    #
    #     When saved, a suffix is added to the file path with the version.
    #     Example: records/<entity_type>_<entity_id>/reminder_<IZ>_<reminder_id>_<version>.xml
    #
    #     :return: object :class:`almapiwrapper.reminder.Reminder`
    #     """
    #     filepath = f'records/{self.zone}_{self.reminder_id}/reminder_{self.zone}_{self.reminder_id}.json'
    #     self._save_from_path(filepath)
    #     return self
    #
    # @check_error
    # def update(self) -> 'Reminder':
    #     """update() -> 'Reminder'
    #     Update the reminder
    #     """
    #     r = self._api_call('put',
    #                        f'{self.api_base_url}/conf/reminders/{self.reminder_id}',
    #                        headers=self._get_headers(),
    #                        data=bytes(self))
    #
    #     if r.ok:
    #         logging.info(f'{repr(self)}: reminder updated.')
    #     else:
    #         self._handle_error(r, 'failed to update reminder')
    #
    #     return self
    #
    # @check_error
    # def delete(self) -> None:
    #     """delete() -> None
    #     Delete the reminder
    #
    #     :return: None
    #     """
    #     r = self._api_call('delete',
    #                        f'{self.api_base_url}/conf/reminders/{self.reminder_id}',
    #                        headers=self._get_headers())
    #
    #     if r.ok:
    #         logging.info(f'{repr(self)}: reminder deleted.')
    #     else:
    #         self._handle_error(r, 'failed to delete reminder')
    #
    # @check_error
    # def get_reminder_id(self) -> str:
    #     """get_reminder_id() -> str
    #     Get the reminder id
    #
    #     :return: string
    #     """
    #     return self.data['id']
    #
    # @check_error
    # def _create_reminder(self) -> 'Reminder':
    #     """create() -> 'Reminder'
    #     Create the reminder
    #
    #     :return: object :class:`almapiwrapper.reminder.Reminder`
    #     """
    #     r = self._api_call('post',
    #                        f'{self.api_base_url}/conf/reminders',
    #                        headers=self._get_headers(),
    #                        data=bytes(self))
    #
    #     if r.ok:
    #         self.data = JsonData(r.json())
    #         self.reminder_id = self.get_reminder_id()
    #         logging.info(f'{repr(self)}: reminder created.')
    #     else:
    #         print(r.text)
    #         self._handle_error(r, 'failed to create reminder')
    #
    #     return self
    #
    # @property
    # @check_error
    # def entity_id(self) -> str:
    #     """entity_id() -> str
    #     Get the entity id
    #
    #     :return: string containing the entity id
    #     """
    #     return self.data['entity']['entity_id']
    #
    # @entity_id.setter
    # @check_error
    # def entity_id(self, entity_id: str) -> None:
    #     """entity_id() -> str
    #     Set the entity id
    #
    #     :return: None
    #     """
    #     self.data['entity']['entity_id'] = entity_id
    #
    # @property
    # @check_error
    # def status(self) -> str:
    #     """status() -> str
    #     Get the status
    #
    #     :return: string containing the status
    #     """
    #     return self.data['status']['value']
    #
    # @status.setter
    # @check_error
    # def status(self, status: str) -> None:
    #     """status() -> str
    #     Set the status
    #
    #     :return: None
    #     """
    #     self.data['status']['value'] = status
    #
    # @property
    # @check_error
    # def reminder_type(self) -> str:
    #     """reminder_type() -> str
    #     Get the reminder type
    #
    #     :return: string containing the reminder type
    #     """
    #     return self.data['type']['value']
    #
    # @reminder_type.setter
    # @check_error
    # def reminder_type(self, reminder_type: str) -> None:
    #     """reminder_type() -> str
    #     Set the reminder type
    #
    #     :return: None
    #     """
    #     self.data['type']['value'] = reminder_type
