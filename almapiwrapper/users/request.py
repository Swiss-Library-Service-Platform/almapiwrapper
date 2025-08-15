from ..record import Record, check_error, JsonData
from typing import Optional, ClassVar, Literal
import logging
import almapiwrapper.users as userslib
from almapiwrapper.inventory import Item
from copy import deepcopy

class Request(Record):
    """Class representing a Users request

    :cvar api_base_url: url of the user api
    :ivar request_id: id of the request
    :ivar zone: initial value: zone of the request
    :ivar env: initial value: environment of the entity: 'P' for production and 'S' for sandbox
    :ivar user: :class:`almapiwrapper.users.User` either primary_id of the user or the user itself must be provided
    :ivar data: :class:`almapiwrapper.record.JsonData` with request data
    """

    api_base_url: ClassVar[str] = 'https://api-eu.hosted.exlibrisgroup.com/almaws/v1'

    def __init__(self,
                 request_id: Optional[str] = None,
                 user_id: Optional[str] = None,
                 zone: Optional[str] = None,
                 env: Optional[Literal['P', 'S']] = 'P',
                 user: Optional[userslib.User] = None,
                 data: Optional[JsonData] = None):
        """Constructor of Request Object

        """
        # Set user_id if provided
        self._user_id = user_id

        # Fetch env and zone from user if available
        if user is not None:
            zone = user.zone
            env = user.env

        super().__init__(zone, env, data)
        self.area = 'Users'
        self.format = 'json'

        self._request_id = request_id

        if user is not None:
            self._user_id = user.primary_id
            self.user = deepcopy(user)
        elif user_id is not None:
            self._user_id = user_id
            self.user = userslib.User(self._user_id, self.zone, self.env)
        elif data is not None and 'user_primary_id' in data.content:
            self._user_id = data.content['user_primary_id']
            self.user = userslib.User(self._user_id, self.zone, self.env)
        elif request_id is not None:
            self._user_id = None
            self.user = None
        else:
            logging.error('Missing information to construct a Request')
            self.error = True

    def __repr__(self):
        """Get a string representation of the object. Useful for logs.
        :return: str
        """
        return f"{self.__class__.__name__}('{self.request_id}', '{self.user.primary_id}', '{self.zone}', '{self.env}')"

    @property
    def request_id(self) -> str:
        """Property returning the loan ID

        It fetches it in a private attribute if not available
        in the data property.
        """
        if self._data is not None and 'request_id' in self.data:
            return self.data['request_id']
        else:
            return self._request_id

    def _fetch_data(self) -> Optional[JsonData]:
        """Fetch the json data of the loan

        :return: :class:`almapiwrapper.record.JsonData`"""
        r = self._api_call('get',
                           f'{self.api_base_url}/users/'
                           f'{self.user.primary_id if self._user_id is not None else "ALL"}/requests/'
                           f'{self.request_id}',
                           headers=self._get_headers())
        if r.ok is True:

            request_data = r.json()
            if self._user_id is None:
                self._user_id = request_data['user_primary_id']
                self.user = userslib.User(self._user_id, self.zone, self.env)
            logging.info(f'{repr(self)}: request data available')
            return JsonData(request_data)

        else:
            self._handle_error(r, f'{repr(self)}: unable to fetch user request')

    @check_error
    def create(self) -> 'userslib.Request':
        """create(self) -> 'userslib.Request'
        Create a new request

        Requests are created only at title level. MMS ID is required in request data
        to create a request.

        :return: object :class:`almapiwrapper.users.Request`"""

        # Decides if request is on item or on title level
        if 'item_id' in self.data and len(self.data['item_id']) > 0:
            params = {'item_pid': self.data['item_id']}
        else:
            params = {'mms_id': self.data['mms_id']}

        r = self._api_call('post',
                           f'{self.api_base_url}/users/{self.user.primary_id}/requests',
                           params=params,
                           headers=self._get_headers(),
                           data=bytes(self))

        if r.ok is True:
            self.data = JsonData(r.json())
            logging.info(f'{repr(self)}: request created')
        else:
            self._handle_error(r, f'{repr(self)}: unable to create request')
        return self

    # @check_error
    # def _fetch_item(self) -> Item:
    #     """Fetch the loaned item
    #
    #     :return: :class:`almapiwrapper.inventory.Item`"""
    #     return Item(self.data['mms_id'],
    #                 self.data['holding_id'],
    #                 self.data['item_id'],
    #                 self.zone,
    #                 self.env)
    #
    # @check_error
    # def return_loan(self):
    #     pass
    #
    # def renew_loan(self) -> 'userslib.Loan':
    #     """Renew the loan
    #
    #     :return: object :class:`almapiwrapper.users.Loan`"""
    #     params = {'op': 'renew'}
    #     r = self._api_call('post',
    #                        f'{self.api_base_url_users}/{self.user.primary_id}/loans/{self.loan_id}',
    #                        headers=self._get_headers(),
    #                        data='{}',
    #                        params=params)
    #
    #     if r.ok is True:
    #         self.data = JsonData(r.json())
    #         if self.data['last_renew_status']['desc'] == 'Renewed Successfully':
    #             logging.info(f'{repr(self)}: loan renewed => new due date: {self.data["due_date"]}')
    #         else:
    #             logging.warning(f'{repr(self)}: loan not renewed: {self.data["last_renew_status"]["desc"]}')
    #     else:
    #         self._handle_error(r, f'{repr(self)}: unable to renew loan')
    #     return self
    #
    # @check_error
    # def change_due_date(self, new_due_date: str) -> 'userslib.Loan':
    #     """Change due date of the loan
    #
    #     :param new_due_date: str : new due date in format YYYY-MM-DD
    #
    #     :return: object :class:`almapiwrapper.users.Loan`"""
    #     # self.data['due_date'] = new_due_date
    #     r = self._api_call('put',
    #                        f'{self.api_base_url_users}/{self.user.primary_id}/loans/{self.loan_id}',
    #                        headers=self._get_headers(),
    #                        data=bytes(JsonData(content={'due_date': new_due_date})))
    #
    #     if r.ok is True:
    #         self.data = JsonData(r.json())
    #         logging.info(f'{repr(self)}: due date changed to {new_due_date}')
    #     else:
    #         self._handle_error(r, f'{repr(self)}: unable to change due date of the loan')
    #     return self
    #
    # @check_error
    # def return_loan(self):
    #     pass

    @check_error
    def cancel(self, reason: Optional[str] = 'CannotBeFulfilled',
               note: Optional[str] = None,
               notify_user: Optional[bool]=True) -> None:
        """cancel(self, reason: Optional[str] = 'Cancelled by patron', note: Optional[str] = None, notify_user: Optional[bool]=True) -> None
        Cancel the request

        :param reason: str : reason for the cancellation
        :param note: str : note for the cancellation
        :param notify_user: bool : notify the user about the cancellation

        :return: None"""
        params = {'reason': reason,
                  'notify_user': notify_user}
        if note is not None:
            params['note'] = note
        r = self._api_call('delete',
                           f'{self.api_base_url}/users/{self.user.primary_id}/requests/{self.request_id}',
                           headers=self._get_headers(),
                           params=params)

        if r.ok is True:
            logging.info(f'{repr(self)}: request cancelled')
        else:
            self._handle_error(r, f'{repr(self)}: unable to cancel request')

    @check_error
    def update(self) -> 'Request':
        """Update a request
        :return: object :class:`almapiwrapper.users.Request`
        """

        r = self._api_call('put',
                           f'{self.api_base_url}/users/{self.user.primary_id}/requests/{self.request_id}',
                           headers=self._get_headers(),
                           data=bytes(self))

        if r.ok is True:
            self.data = JsonData(r.json())
            logging.info(f'{repr(self)}: request updated')
        else:
            self._handle_error(r, f'{repr(self)}: unable to update request')
        return self


    @check_error
    def save(self) -> 'userslib.Request':
        """Save a user loan record in the 'records' folder

        When saved, a suffix is added to the file path with the version.
        Example: records/<primary_id>/request_<IZ>_<request_id>_<version>.xml

        :return: object :class:`almapiwrapper.users.Request`
        """
        filepath = f'records/{self.user.primary_id}/request_{self.zone}_{self.request_id}.json'
        self._save_from_path(filepath)
        return self
