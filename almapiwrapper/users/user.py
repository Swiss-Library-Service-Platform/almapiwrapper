"""This module allows getting information and changing Alma users"""

from typing import Optional, ClassVar, Literal, Union
import logging
import requests
from ..record import Record, check_error, JsonData


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

    def save(self) -> 'User':
        """Save a user record in the 'records' folder

        When saved, a suffix is added to the file path with the version.
        Example: records/NZ_991170519490005501/bib991170519490005501_01.xml

        :return: object :class:`almapiwrapper.users.User`
        """
        filepath = f'records/{self.zone}/user_{self.primary_id}.json'
        self._save_from_path(filepath)
        return self

    @check_error
    def update(self) -> 'User':
        """update() -> 'User'
        Update the user through api

        :return: object :class:`almapiwrapper.users.User`

        .. note::
            If the record encountered an error, this
            method will be skipped.
        """
        r = requests.put(f'{self.api_base_url}/{self.primary_id}',
                         data=bytes(self),
                         headers=self._get_headers())
        if r.ok:
            logging.info(f'{repr(self)}: user updated.')
        else:
            self._handle_error(r, 'failed to delete user')

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
            the password will be set at the default value
        :return: object :class:`almapiwrapper.users.User` or object :class:`almapiwrapper.users.NewUser` (in case of error)

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
        if password is None:
            password = '123pw123'
        self.data['password'] = password

        return self


if __name__ == "__main__":
    pass
