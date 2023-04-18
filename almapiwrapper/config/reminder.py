"""This module allow to create and manage sets in Alma"""
from typing import Literal, Optional, List, Dict, Union
import logging
from ..record import JsonData, Record, check_error
import requests


def fetch_reminders(zone: str,
                    env: Optional[Literal['P', 'S']] = 'P',
                    reminder_type: Optional[str] = None,
                    reminder_status: Optional[str] = None,
                    from_date: Optional[str] = None,
                    to_date: Optional[str] = None,
                    entity_id: Optional[str] = None) -> List['Reminder']:
    """This function fetch the data describing the reminders.

    :param zone: zone of the fee
    :param env: environment of the entity: 'P' for production and 'S' for sandbox
    :param reminder_type: filter by reminder type
    :param reminder_status: filter by reminder status
    :param from_date: filter by date from, format: YYYY-MM-DD
    :param to_date: filter by date to, format: YYYY-MM-DD
    :param entity_id: filter by entity id, for example mms_id for bib records
    :return: List of :class:`almapiwrapper.config.reminder.Reminder`
    """

    # Prepare params and filters
    params = {'limit': 100}
    if reminder_type is not None:
        params['type'] = reminder_type
    if reminder_status is not None:
        params['status'] = reminder_status
    if from_date is not None:
        params['from'] = from_date
    if to_date is not None:
        params['to'] = to_date
    if entity_id is not None:
        params['entity_id'] = entity_id

    reminders = []

    # Init counters
    offset = 0
    nb_total_records = 0

    # Handle offset if more than 100 results are available
    while offset == 0 or offset < nb_total_records:

        # Make request
        params['offset'] = offset

        r = requests.get(f'{Reminder.api_base_url}/conf/reminders',
                         params=params,
                         headers=Record.build_headers(data_format='json', env=env,
                                                      zone=zone, rights='RW', area='Conf'))

        # Check result
        if r.ok is True:
            reminders_list = JsonData(r.json())
            nb_total_records = int(reminders_list.content['total_record_count'])

            if 'reminder' in reminders_list.content and reminders_list.content['reminder'] is not None:
                reminders += [Reminder(reminder['id'], zone, env) for reminder in reminders_list.content['reminder']]
                nb_reminders = len(reminders_list.content['reminder'])
            else:
                nb_reminders = 0

            logging.info(f'fetch_reminders("{zone}", "{env}"): '
                         f'{offset + nb_reminders} / '
                         f'{nb_total_records} users data available')
            offset += 100

        else:
            _handle_error(r, 'unable to fetch reminder data', zone, env)

    return reminders


def _handle_error(r: requests.models.Response, msg: str, zone: str, env: str):
    """Set the record error attribute to True and write the logs about the error

    :param r: request response of the api
    :param msg: context message of the error
    :return: None
    """
    json_data = r.json()
    print(json_data)
    print(r.url)
    error_message = json_data['errorList']['error'][0]['errorMessage']

    logging.error(f'fetch_reminders({zone}, {env}) - {r.status_code}: '
                  f'{msg} / {error_message}')


class Reminder(Record):
    """Class representing a reminder
    """

    def __init__(self,
                 reminder_id: Optional[str] = None,
                 zone: Optional[str] = None,
                 env: Optional[Literal['P', 'S']] = 'P',
                 data: Optional[Union[Dict, JsonData]] = None,
                 create_reminder: Optional[bool] = False) -> None:
        """Constructor of `Reminder`

        :param reminder_id: reminder id
        :param zone: zone of the reminder
        :param env: environment of the reminder: 'P' for production and 'S' for sandbox
        :param data: data of the reminder, :class:`almapiwrapper.record.JsonData` object
        :param create_reminder: if True create the reminder in Alma
        """
        super().__init__(zone, env, data)
        self.area = 'Conf'
        self.format = 'json'
        self.reminder_id = reminder_id

        if data is not None:
            if not isinstance(data, JsonData):
                data = JsonData(data)
            self.data = data

        if create_reminder is True:
            self._create_reminder()

    def _fetch_data(self) -> Optional[JsonData]:
        """This method fetch the data describing the reminder.

        :return: :class:`almapiwrapper.record.JsonData` object
        """
        r = self._api_call('get',
                           f'{self.api_base_url}/conf/reminders/{self.reminder_id}',
                           headers=self._get_headers())
        if r.ok is True:
            logging.info(f'{repr(self)}: reminder data available')
            return JsonData(r.json())
        else:
            self._handle_error(r, 'unable to fetch reminder data')

    def __repr__(self) -> str:
        """Get a string representation of the object. Useful for logs.

        :return: string
        """
        return f"{self.__class__.__name__}('{self.reminder_id}', '{self.zone}', '{self.env}')"

    @check_error
    def save(self) -> 'Reminder':
        """save() -> 'Reminder'
        Save a Reminder record in the 'records' folder

        When saved, a suffix is added to the file path with the version.
        Example: records/<entity_type>_<entity_id>/reminder_<IZ>_<reminder_id>_<version>.xml

        :return: object :class:`almapiwrapper.reminder.Reminder`
        """
        filepath = f'records/{self.zone}_{self.reminder_id}/reminder_{self.zone}_{self.reminder_id}.json'
        self._save_from_path(filepath)
        return self

    @check_error
    def update(self) -> 'Reminder':
        """update() -> 'Reminder'
        Update the reminder
        """
        r = self._api_call('put',
                           f'{self.api_base_url}/conf/reminders/{self.reminder_id}',
                           headers=self._get_headers(),
                           data=bytes(self))

        if r.ok:
            logging.info(f'{repr(self)}: reminder updated.')
        else:
            self._handle_error(r, 'failed to update reminder')

        return self

    @check_error
    def delete(self) -> None:
        """delete() -> None
        Delete the reminder

        :return: None
        """
        r = self._api_call('delete',
                           f'{self.api_base_url}/conf/reminders/{self.reminder_id}',
                           headers=self._get_headers())

        if r.ok:
            logging.info(f'{repr(self)}: reminder deleted.')
        else:
            self._handle_error(r, 'failed to delete reminder')

    @check_error
    def get_reminder_id(self) -> str:
        """get_reminder_id() -> str
        Get the reminder id

        :return: string
        """
        return self.data['id']

    @check_error
    def _create_reminder(self) -> 'Reminder':
        """create() -> 'Reminder'
        Create the reminder

        :return: object :class:`almapiwrapper.reminder.Reminder`
        """
        r = self._api_call('post',
                           f'{self.api_base_url}/conf/reminders',
                           headers=self._get_headers(),
                           data=bytes(self))

        if r.ok:
            self.data = JsonData(r.json())
            self.reminder_id = self.get_reminder_id()
            logging.info(f'{repr(self)}: reminder created.')
        else:
            print(r.text)
            self._handle_error(r, 'failed to create reminder')

        return self

    @property
    @check_error
    def entity_id(self) -> str:
        """entity_id() -> str
        Get the entity id

        :return: string containing the entity id
        """
        return self.data['entity']['entity_id']

    @entity_id.setter
    @check_error
    def entity_id(self, entity_id: str) -> None:
        """entity_id() -> str
        Set the entity id

        :return: None
        """
        self.data['entity']['entity_id'] = entity_id

    @property
    @check_error
    def status(self) -> str:
        """status() -> str
        Get the status

        :return: string containing the status
        """
        return self.data['status']['value']

    @status.setter
    @check_error
    def status(self, status: str) -> None:
        """status() -> str
        Set the status

        :return: None
        """
        self.data['status']['value'] = status

    @property
    @check_error
    def reminder_type(self) -> str:
        """reminder_type() -> str
        Get the reminder type

        :return: string containing the reminder type
        """
        return self.data['type']['value']

    @reminder_type.setter
    @check_error
    def reminder_type(self, reminder_type: str) -> None:
        """reminder_type() -> str
        Set the reminder type

        :return: None
        """
        self.data['type']['value'] = reminder_type
