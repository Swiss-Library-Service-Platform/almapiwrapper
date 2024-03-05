from ..record import Record, check_error, JsonData
from typing import Optional, ClassVar, Literal
import logging
import almapiwrapper.users as userslib
from almapiwrapper.inventory import Item

class Loan(Record):
    """Class representing a Users loan

    :cvar api_base_url_users: url of the user api
    :ivar loan_id: id of the loan
    :ivar item: :class:`almapiwrapper.inventory.Item` loaned item
    :ivar zone: initial value: zone of the fee
    :ivar env: initial value: environment of the entity: 'P' for production and 'S' for sandbox
    :ivar user: :class:`almapiwrapper.users.User` either primary_id of the user or the user itself must be provided
    :ivar data: :class:`almapiwrapper.record.JsonData` with fee data
    """

    api_base_url_users: ClassVar[str] = 'https://api-eu.hosted.exlibrisgroup.com/almaws/v1/users'

    def __init__(self,
                 loan_id: Optional[str] = None,
                 primary_id: Optional[str] = None,
                 zone: Optional[str] = None,
                 env: Optional[Literal['P', 'S']] = 'P',
                 user: Optional[userslib.User] = None,
                 data: Optional[JsonData] = None):
        """Constructor of Loan Object

        """
        # Fetch env and zone from user if available
        if user is not None:
            zone = user.zone
            env = user.env

        super().__init__(zone, env, data)
        self.area = 'Users'
        self.format = 'json'

        self._loan_id = loan_id
        self._item = None

        if primary_id is not None:
            self.user = userslib.User(primary_id, self.zone, self.env)
        elif user is not None:
            self.user = user
        else:
            logging.error('Missing information to construct a Loan')
            self.error = True

    def __repr__(self):
        """Get a string representation of the object. Useful for logs.
        :return: str
        """
        return f"{self.__class__.__name__}('{self.loan_id}', '{self.user.primary_id}', '{self.zone}', '{self.env}')"

    @property
    def loan_id(self) -> str:
        """Property returning the loan ID

        It fetches it in a private attribute if not available
        in the data property.
        """
        if self._data is not None:
            return self.data['loan_id']
        else:
            return self._loan_id

    @property
    def item(self) -> Optional[Item]:
        """Property returning the loaned item

        It fetches it in a private attribute if not available
        in the data property.
        """
        if self._item is None:
            item = self._fetch_item()
            if self.error is False:
                self._item = item

        return self._item

    def _fetch_data(self) -> Optional[JsonData]:
        """Fetch the json data of the loan

        :return: :class:`almapiwrapper.record.JsonData`"""
        r = self._api_call('get',
                           f'{self.api_base_url_users}/{self.user.primary_id}/loans/{self.loan_id}',
                           headers=self._get_headers())
        if r.ok is True:
            logging.info(f'{repr(self)}: loan data available')
            loan_data = r.json()

            return JsonData(loan_data)

        else:
            self._handle_error(r, f'{repr(self)}: unable to fetch user loan')

    @check_error
    def _fetch_item(self) -> Item:
        """Fetch the loaned item

        :return: :class:`almapiwrapper.inventory.Item`"""
        return Item(self.data['mms_id'],
                    self.data['holding_id'],
                    self.data['item_id'],
                    self.zone,
                    self.env)

    @check_error
    def return_loan(self):
        pass

    def renew_loan(self) -> 'userslib.Loan':
        """Renew the loan

        :return: object :class:`almapiwrapper.users.Loan`"""
        params = {'op': 'renew'}
        r = self._api_call('post',
                           f'{self.api_base_url_users}/{self.user.primary_id}/loans/{self.loan_id}',
                           headers=self._get_headers(),
                           data='{}',
                           params=params)

        if r.ok is True:
            self.data = JsonData(r.json())
            if self.data['last_renew_status']['desc'] == 'Renewed Successfully':
                logging.info(f'{repr(self)}: loan renewed => new due date: {self.data["due_date"]}')
            else:
                logging.warning(f'{repr(self)}: loan not renewed: {self.data["last_renew_status"]["desc"]}')
        else:
            self._handle_error(r, f'{repr(self)}: unable to renew loan')
        return self

    @check_error
    def change_due_date(self, new_due_date: str) -> 'userslib.Loan':
        """Change due date of the loan

        :param new_due_date: str : new due date in format YYYY-MM-DD

        :return: object :class:`almapiwrapper.users.Loan`"""
        # self.data['due_date'] = new_due_date
        r = self._api_call('put',
                           f'{self.api_base_url_users}/{self.user.primary_id}/loans/{self.loan_id}',
                           headers=self._get_headers(),
                           data=bytes(JsonData(content={'due_date': new_due_date})))

        if r.ok is True:
            self.data = JsonData(r.json())
            logging.info(f'{repr(self)}: due date changed to {new_due_date}')
        else:
            self._handle_error(r, f'{repr(self)}: unable to change due date of the loan')
        return self

    @check_error
    def return_loan(self):
        pass

    @check_error
    def save(self) -> 'userslib.Loan':
        """Save a user loan record in the 'records' folder

        When saved, a suffix is added to the file path with the version.
        Example: records/<primary_id>/loan_<IZ>_<loan_id>_<version>.xml

        :return: object :class:`almapiwrapper.users.Fee`
        """
        filepath = f'records/{self.user.primary_id}/loan_{self.zone}_{self.loan_id}.json'
        self._save_from_path(filepath)
        return self

