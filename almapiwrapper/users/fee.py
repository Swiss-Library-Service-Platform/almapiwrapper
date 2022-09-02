from ..record import Record, check_error, JsonData
from typing import Optional, ClassVar, Literal
import requests
import logging
import almapiwrapper.users as userslib


class Fee(Record):
    """Class representing a Users fee

    :cvar api_base_url_users: url of the user api
    :ivar fee_id: id of the fee
    :ivar primary_id: primary_id of the user
    :ivar zone: initial value: zone where the user should be created
    :ivar env: initial value: environment of the entity: 'P' for production and 'S' for sandbox
    :ivar user: :class:`almapiwrapper.users.User` either primary_id of the user or the user itself must be provided
    :ivar data: :class:`almapiwrapper.record.JsonData` with fee data"""

    api_base_url_users: ClassVar[str] = 'https://api-eu.hosted.exlibrisgroup.com/almaws/v1/users'

    def __init__(self,
                 fee_id: Optional[str] = None,
                 primary_id: Optional[str] = None,
                 zone: Optional[str] = None,
                 env: Optional[Literal['P', 'S']] = 'P',
                 user: Optional[userslib.User] = None,
                 data: Optional[JsonData] = None,
                 create_fee: Optional[bool] = False):
        """Constructor of Fee Object
        """
        # Fetch env and zone from user if available
        if user is not None:
            zone = user.zone
            env = user.env

        super().__init__(zone, env, data)
        self.area = 'Users'
        self.format = 'json'
        self._fee_id = fee_id
        if primary_id is not None:
            self.user = userslib.User(primary_id, self.zone, self.env)
        elif user is not None:
            self.user = user
        else:
            logging.error('Missing information to construct a Fee')
            self.error = True

        if create_fee is True:
            self._create_fee()

    def __repr__(self) -> str:
        """Get a string representation of the object. Useful for logs.
        :return: str
        """
        return f"{self.__class__.__name__}('{self.fee_id}', '{self.user.primary_id}', '{self.zone}', '{self.env}')"

    def _fetch_data(self) -> Optional[JsonData]:
        """Fetch the json data of the fee

        :return: :class:`almapiwrapper.record.JsonData`"""
        r = requests.get(f'{self.api_base_url_users}/{self.user.primary_id}/fees/{self.fee_id}',
                         headers=self._get_headers())
        if r.ok is True:
            logging.info(f'{repr(self)}: fee data available')
            fee_data = r.json()

            return JsonData(fee_data)

        else:
            self._handle_error(r, f'{repr(self)}: unable to fetch user fee')

    @property
    def fee_id(self) -> str:
        """Property returning the fee ID

        It fetches it in a private attribute if not available
        in the data property.
        """
        if self._data is not None:
            return self.data['id']
        else:
            return self._fee_id

    def _create_fee(self):
        """Create a fee to the user with the provided data.

        :return: object :class:`almapiwrapper.users.Fee`
        """
        r = requests.post(f'{self.api_base_url_users}/{self.user.primary_id}/fees',
                          headers=self._get_headers(),
                          data=bytes(self))
        if r.ok is True:
            self.data = JsonData(r.json())
            logging.info(f'{repr(self)}: fee created')
        else:
            self._handle_error(r, 'unable to create the new fee')

    @check_error
    def save(self) -> 'userslib.Fee':
        """Save a user fee record in the 'records' folder

        When saved, a suffix is added to the file path with the version.
        Example: records/<primary_id>/fee_<IZ>_<fee_id>_<version>.xml

        :return: object :class:`almapiwrapper.users.Fee`
        """
        filepath = f'records/{self.user.primary_id}/fee_{self.zone}_{self.fee_id}.json'
        self._save_from_path(filepath)
        return self

    @check_error
    def operate(self,
                op: Literal['pay', 'waive', 'dispute', 'restore'],
                amount: Optional[float] = None,
                comment: Optional[str] = None,
                method: Literal['CREDIT_CARD', 'ONLINE', 'CASH'] = None,
                reason: Optional[str] = None,
                external_transaction_id: Optional[str] = None):
        """Operate on a fee

        :param op: can be 'pay', 'waive', 'dispute', 'restore'
        :param amount: optional amount. For pay and waive, it will be the balance as default value
        :param comment: free text associated to the operation
        :param method: for pay or waive operations, can be: 'CREDIT_CARD', 'ONLINE', 'CASH'
        :param reason: a value of FineFeeTransactionReason table. Required only for waiving fee
        :param external_transaction_id: external id of the bursar system

        :return: object :class:`almapiwrapper.users.Fee`
        """
        # Per default pay the entire fee
        if op in ['pay', 'waive'] and amount is None:
            amount = self.data['balance']

        # Set a default payment method if required
        if op == 'pay' and method is None:
            method = 'ONLINE'

        # Set a default value for reason when waiving fees
        if op == 'waive' and reason is None:
            reason = 'OTHER'

        r = requests.post(f'{self.api_base_url_users}/{self.user.primary_id}/fees/{self.fee_id}',
                          headers=self._get_headers(),
                          data=None,
                          params={'op': op,
                                  'amount': str(amount),
                                  'comment': comment,
                                  'method': method,
                                  'reason': reason,
                                  'external_transaction_id': external_transaction_id})
        if r.ok is True:
            self.data = JsonData(r.json())
            logging.info(f'{repr(self)}: fee operation "{op}" succeed')
        else:
            self._handle_error(r, f'{repr(self)}: fee operation "{op}" failed')

        return self


if __name__ == "__main__":
    pass
