"""This module allows getting information and changing Alma users"""

from typing import Optional, ClassVar, Literal, Union, List
import logging

import almapiwrapper.inventory

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
        self.format = 'json'
        self._fees = None
        self._loans = None

    def __repr__(self) -> str:
        """Get a string representation of the object. Useful for logs.
        :return: string
        """
        return f"{self.__class__.__name__}('{self.primary_id}', '{self.zone}', '{self.env}')"

    def _fetch_data(self) -> Optional[JsonData]:
        """Use API to fetch user data

        :return: json data or None if no data is available
        """

        r = self._api_call('get',
                           f'{self.api_base_url}/{self.primary_id}',
                           headers=self._get_headers())
        if r.ok is True:
            logging.info(f'{repr(self)}: user data available')
            return JsonData(r.json())
        else:
            self._handle_error(r, f'unable to fetch user data')

    def _fetch_fees(self) -> Optional[List['users.Fee']]:
        """Fetch fee data of the current user

        :return: list of :class:`almapiwrapper.users.Fee` objects"""

        r = self._api_call('get',
                           f'{self.api_base_url}/{self.primary_id}/fees',
                           # params={'status': 'EXPORTED'},
                           headers=self._get_headers())
        if r.ok is True:

            logging.info(f'{repr(self)}: fees data available')
            fees_data = r.json()
            if 'fee' not in fees_data or fees_data['fee'] is None:
                logging.warning(f'{repr(self)}: no fee in the account')
                return []
            fees = []
            for fee_data in fees_data['fee']:
                fees.append(users.Fee(user=self, data=JsonData(fee_data)))
            return fees
        else:
            self._handle_error(r, f'unable to fetch user fees')

    def _fetch_loans(self) -> Optional[List['users.Loan']]:
        """Fetch loan data of the current user

        :return: list of :class:`almapiwrapper.users.Loan` objects"""

        r = self._api_call('get',
                           f'{self.api_base_url}/{self.primary_id}/loans',
                           params={'limit': '100'},
                           headers=self._get_headers())
        if r.ok is True:

            logging.info(f'{repr(self)}: loans data available')
            loans_data = r.json()
            if 'item_loan' not in loans_data or loans_data['item_loan'] is None:
                logging.warning(f'{repr(self)}: no loan in the account')
                return []
            loans = []
            for loan_data in loans_data['item_loan']:
                loans.append(users.Loan(user=self, data=JsonData(loan_data)))
            return loans
        else:
            self._handle_error(r, f'unable to fetch user loans')

    def save(self) -> 'User':
        """save() -> 'User'
        Save a user record in the 'records' folder

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

        r = self._api_call('put',
                           f'{self.api_base_url}/{self.primary_id}',
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
        r = self._api_call('delete',
                           f'{self.api_base_url}/{self.primary_id}',
                           headers=self._get_headers())
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

        return self._primary_id

    @primary_id.setter
    def primary_id(self, primary_id) -> None:
        """Set the primary ID

        If json data is available, change the primary ID
        at the data level. To modify the primary ID of the user,
        do not use this method property but change directly the primary_id
        in the data attribute.

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

    @property
    def loans(self) -> Optional[List['users.Loan']]:
        """Property returning the list of the loans of the user

        :return: list of :class:`almapiwrapper.users.Loan` objects"""
        if self._loans is None:
            self._loans = self._fetch_loans()

        return self._loans

    @check_error
    def create_loan(self,
                    library: str,
                    circ_desk: str,
                    item_barcode: Optional[str] = None,
                    item_id: Optional[str] = None,
                    item: Optional[almapiwrapper.inventory.Item] = None) -> Optional['users.Loan']:
        """create_loan(library: str, circ_desk: str, item_barcode: Optional[str] = None, item_id: Optional[str] = None, item: Optional[almapiwrapper.inventory.Item] = None) -> Optional['users.Loan']

        Create a loan for the user

        :param library: code of the library
        :param circ_desk: code of the circulation desk
        :param item_barcode: barcode of the item
        :param item_id: id of the item
        :param item: object :class:`almapiwrapper.inventory.Item`

        :return: object :class:`almapiwrapper.users.Loan`

        .. note::
            If the record encountered an error, this
            method will be skipped.
        """
        if item is not None and item.error is False:
            item_barcode = item.barcode

        # Check if mandatory fields are available
        if library is None or circ_desk is None or (item_barcode is None and item_id is None):
            logging.error('Missing information to create a loan')
            self.error = True
            return None

        # Create the loan
        loan_data = {"circ_desk": {"value": circ_desk},
                     "library": {"value": library}}

        params = {'item_barcode': item_barcode} if item_barcode is not None else {'item_pid': item_id}

        r = self._api_call('post',
                           f'{self.api_base_url}/{self.primary_id}/loans',
                           params=params,
                           data=bytes(JsonData(loan_data)),
                           headers=self._get_headers())
        if r.ok is True:
            loan_data = JsonData(r.json())

            loan = users.Loan(user=self, data=loan_data)

            logging.info(f'{repr(self)}: {repr(loan)} created.')

            return loan
        else:
            self._handle_error(r, f'unable to create loan for '
                                  f'{item_barcode if item_barcode is not None else item_id} '
                                  f'on {circ_desk} at {library}')

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
        """add_synchro_note() -> 'User'
        Add a test synchronization notes

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
        """remove_synchro_note() -> 'User'
        Remove all test synchronization notes

        :return: object :class:`almapiwrapper.users.User`"""
        nb_notes = len(self.data['user_note'])
        self.data['user_note'] = [note for note in self.data['user_note']
                                  if not note['note_text'].startswith('SLSP Test-synchronisation')]
        nb_sup_notes = nb_notes - len(self.data['user_note'])

        if nb_sup_notes > 0:
            self.update()
            if self.error is False:
                logging.info(f'{repr(self)}: {nb_sup_notes} synchronization test note(s) deleted')
        else:
            logging.warning(f'{repr(self)}: NO synchronization test note deleted')

        return self

    @check_error
    def check_synchro_note(self) -> bool:
        """check_synchro_note() -> bool
        Test if the user has a synchronization test note

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
        self._primary_id = self.data['primary_id']
        self.area = 'Users'
        self.format = 'json'

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

        r = self._api_call('post',
                           f'{self.api_base_url}',
                           headers=self._get_headers(),
                           data=bytes(self))

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

        if password is not None:
            self.data['password'] = password

        return self


if __name__ == "__main__":
    pass
