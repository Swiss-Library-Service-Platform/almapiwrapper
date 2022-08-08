"""This module allows getting information and changing Alma users"""

from typing import Optional, ClassVar, Literal, Union, List
import logging
import requests
from ..record import Record, check_error, JsonData
import almapiwrapper.users as users
from datetime import datetime


class User(Record):
    """Class representing an Alma user

    :ivar primary_id: initial value: primary_id of the user
    :ivar zone: initial value: zone where the user should be created
    :ivar env: initial value: environment of the entity: 'P' for production and 'S' for sandbox
    :ivar data: initial value: :class:`almapiwrapper.record.JsonData` of the user (useful for new created users)

    """

    api_base_url: ClassVar[str] = 'https://api-eu.hosted.exlibrisgroup.com/almaws/v1/users'

    def __init__(self,
                 primary_id: str,
                 zone: str,
                 env: Optional[Literal['P', 'S']] = 'P',
                 data: Optional[JsonData] = None) -> None:
        """Constructor for user
        """
        super().__init__(zone, env, data)
        self.primary_id = primary_id
        self.area = 'Users'
        self._fees = None

    def __repr__(self) -> str:
        """Get a string representation of the object. Useful for logs.
        :return: string
        """
        return f"{self.__class__.__name__}('{self.primary_id}', '{self.zone}', '{self.env}')"

    def _fetch_data(self) -> Optional[JsonData]:
        """Use API to fetch user data
        :return: json data or None if no data is available
        """

        r = requests.get(f'{self.api_base_url}/{self.primary_id}', headers=self._get_headers())
        if r.ok is True:
            logging.info(f'{repr(self)}: user data available')
            return JsonData(r.json())
        else:
            self._handle_error(r, f'unable to fetch user data')

    def _fetch_fees(self) -> Optional[List['users.Fee']]:
        """Fetch fee data of the current user
        :return: list of :class:`almapiwrapper.users.Fee` objects"""

        r = requests.get(f'{self.api_base_url}/{self.primary_id}/fees', headers=self._get_headers())
        if r.ok is True:

            logging.info(f'{repr(self)}: fees data available')
            fees_data = r.json()
            if 'fee' not in fees_data:
                logging.warning(f'{repr(self)}: no fee in the account')
                return []
            fees = []
            for fee_data in fees_data['fee']:
                fees.append(users.Fee(user=self, data=JsonData(fee_data)))
            return fees
        else:
            self._handle_error(r, f'unable to fetch user fees')

    def save(self) -> 'User':
        """Save a user record in the 'records' folder

        When saved, a suffix is added to the file path with the version.
        Example: records/<primary_id>/user_<IZ>_<primary_id>_<version>.xml

        :return: object :class:`almapiwrapper.users.User`
        """
        filepath = f'records/{self.primary_id}/user_{self.zone}_{self.primary_id}.json'
        self._save_from_path(filepath)
        return self

    @check_error
    def update(self, override: Optional[str] = None) -> 'User':
        """update() -> 'User'
        Update the user through api

        :param override: string containing the list of the fields to override

        :return: object :class:`almapiwrapper.users.User`

        .. note::
            If the record encountered an error, this
            method will be skipped.
        """
        if override is not None:
            params = {'override': override}
        else:
            params = {}

        r = requests.put(f'{self.api_base_url}/{self.primary_id}',
                         data=bytes(self),
                         params=params,
                         headers=self._get_headers())
        if r.ok:
            logging.info(f'{repr(self)}: user updated.')
            self.data = JsonData(r.json())
        else:
            self._handle_error(r, 'failed to update user')

        return self

    @check_error
    def delete(self) -> None:
        """delete()
        Delete the user

        :return: None

        .. note::
            If the record encountered an error, this
            method will be skipped.
        """
        r = requests.delete(f'{self.api_base_url}/{self.primary_id}', headers=self._get_headers())
        if r.ok:
            logging.info(f'{repr(self)}: user deleted.')
        else:
            self._handle_error(r, 'failed to delete user')

    @property
    def primary_id(self) -> str:
        """Property returning the primary ID

        It fetches it in a private attribute if not available
        in the data property.

        When a new value is set and json data is available, it changes the primary ID
        at the data level.

        :return: primary ID of the user
        """
        if self._data is not None:
            return self.data['primary_id']
        else:
            return self._primary_id

    @primary_id.setter
    def primary_id(self, primary_id) -> None:
        """Set the primary ID

        If json data is available, change the primary ID
        at the data level.

        :param primary_id: new primary ID to set
        :return: None
        """
        self._primary_id = primary_id
        if self._data is not None:
            self.data['primary_id'] = self._primary_id

    @property
    def fees(self) -> Optional[List['users.Fee']]:
        """Property returning the list of the fees of the user

        :return: list of :class:`almapiwrapper.users.Fee` objects"""
        if self._fees is None:
            self._fees = self._fetch_fees()

        return self._fees

    @check_error
    def set_password(self, password: Optional[str] = '123pw123') -> 'User':
        """set_password(password: Optional[str] = '123pw123') -> 'User'
        Set a new password to a user

        :param password: password string, default is '123pw123'
        :return: object :class:`almapiwrapper.users.User`

        .. note::
            If the record encountered an error, this
            method will be skipped.
        """
        self.data['password'] = password
        self.data['force_password_change'] = "TRUE"

        return self

    @check_error
    def add_synchro_note(self) -> 'User':
        """Add a test synchronization notes

        :return: object :class:`almapiwrapper.users.User`"""

        note = {"note_type": {"value": "OTHER"},
                "note_text": f"SLSP Test-synchronisation {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                "user_viewable": False,
                "popup_note": False,
                "segment_type": "Internal"}
        self.data['user_note'].append(note)
        self.update()
        if self.error is False:
            logging.info(f'{repr(self)}: synchronization test note added')

        return self

    @check_error
    def remove_synchro_note(self) -> 'User':
        """Remove all test synchronization notes

        :return: object :class:`almapiwrapper.users.User`"""
        nb_notes = len(self.data['user_note'])
        self.data['user_note'] = [note for note in self.data['user_note']
                                  if not note['note_text'].startswith('SLSP Test-synchronisation')]
        nb_sup_notes = nb_notes - len(self.data['user_note'])

        if nb_sup_notes > 0:
            self.update()
            if self.error is False:
                logging.info(f'{repr(self)}: {nb_sup_notes} synchronization test note(s) suppressed')
        else:
            logging.warning(f'{repr(self)}: NO synchronization test note suppressed')

        return self

    @check_error
    def check_synchro_note(self) -> bool:
        """Test if the user has a synchronization test note

        :return: True if a synchronization test note is found else False
        """
        has_synchro_note = len([note for note in self.data['user_note']
                                if note['note_text'].startswith('SLSP Test-synchronisation')]) > 0
        if has_synchro_note is True:
            logging.info(f'{repr(self)}: a synchronization test note exists')
        else:
            logging.warning(f'{repr(self)}: NO synchronization test note exists')
        return has_synchro_note


class NewUser(User):
    """Class used to create new users

    :var zone: initial value: zone where the user should be created
    :var env: initial value: environment of the entity: 'P' for production and 'S' for sandbox
    :var data: initial value: :class:`almapiwrapper.record.JsonData` of the user to create
    """

    def __init__(self, zone: str, env: Literal['P', 'S'], data: JsonData):
        """Constructor to create new users
        """
        super(User, self).__init__(zone, env, data)
        self.area = 'Users'

    @check_error
    def create(self, password: Optional[str] = None) -> Union['NewUser', User]:
        """create(password: Optional[str] = None) -> Union['NewUser', User]
        Create the user with API.

        :param password: optional string with the password, if not provided,
            the password will be set at the default value (if not available in the data)
        :return: object :class:`almapiwrapper.users.User` or object :class:`almapiwrapper.users.NewUser`
            (in case of error)

        .. note::
            If the record encountered an error, this
            method will be skipped.
        """
        self.set_password(password)

        r = requests.post(f'{self.api_base_url}', headers=self._get_headers(), data=bytes(self))

        if r.ok is True:
            logging.info(f'{repr(self)}: user created')
            self._data = JsonData(r.json())
            return User(self.primary_id, self.zone, self.env, self._data)
        else:
            self._handle_error(r, f'unable to create user')
            return self

    @check_error
    def set_password(self, password: Optional[str] = None) -> 'NewUser':
        """set_password(password: Optional[str] = None) -> 'NewUser'
        Set the password of a new user

        :param password: string containing the new password.
        :return: object :class:`almapiwrapper.users.NewUser`
        .. note::
            If the record encountered an error, this
            method will be skipped.
        """
        if password is None and self.data['password'] == '':
            password = '123pw123'
        self.data['password'] = password

        return self


if __name__ == "__main__":
    pass
