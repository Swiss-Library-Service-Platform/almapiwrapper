from ..record import Record, check_error, JsonData
from typing import Optional, Literal,ClassVar, List, Union
import almapiwrapper.acquisitions as acquisitionslib
from lxml import etree
import requests
import logging
from json import JSONDecodeError


def _handle_error(q: str, r: requests.models.Response, msg: str, zone: str, env: str):
    """Set the handle errors of the fetch_invoices function

    :param q: str : query to fetch the invoices
    :param r: request response of the api
    :param msg: context message of the error
    :return: None
    """
    try:
        json_data = r.json()
        error_message = json_data['errorList']['error'][0]['errorMessage']
    except JSONDecodeError:
        xml = etree.fromstring(r.content)
        error_message = xml.find('.//{http://com/exlibris/urm/general/xmlbeans}errorMessage').text

    logging.error(f'fetch_invoices("{q}", "{zone}", "{env}") - {r.status_code}: '
                  f'{msg} / {error_message}')

class Invoice(Record):
    """Class representing an Invoice

    :ivar invoice_id: initial value: code of the vendor
    :param invoice_number: initial value: invoice_number of the invoice
    :ivar zone: initial value: zone of the vendor
    :ivar env: initial value: environment of the entity: 'P' for production and 'S' for sandbox
    :ivar data: :class:`almapiwrapper.record.JsonData` with raw vendor data
    """

    api_base_url_invoices: ClassVar[str] = f'{Record.api_base_url}/acq/invoices'

    def __init__(self,
                 invoice_id: Optional[str] = None,
                 zone: Optional[str] = None,
                 env: Literal['P', 'S'] = 'P',
                 invoice_number: Optional[str] = None,
                 data: Optional[Union[dict, JsonData]] = None) -> None:
        """Constructor of Invoice Object
        """

        super().__init__(zone, env)
        self.area = 'Acquisitions'
        self.format = 'json'
        self.invoice_id = invoice_id
        if data is not None:
            self._data = data if type(data) is JsonData else JsonData(data)
        elif invoice_number is not None:
            invoices = fetch_invoices(f'invoice_number~{invoice_number}', zone, env)
            if len(invoices) > 0:
                self._data = JsonData(invoices[0].data)
                self.invoice_id = invoices[0].invoice_id
            else:
                self.error = True
                logging.error(f'No invoice found for invoice_number: {invoice_number}')

        elif invoice_id is not None:
            pass
        else:
            self.error = True
            logging.error('Missing information to construct an Invoice')

    def __repr__(self) -> str:
        """Get a string representation of the object. Useful for logs.

        :return: str representing the object
        """
        return f"{self.__class__.__name__}('{self.invoice_id}', '{self.zone}', '{self.env}')"

    @property
    def invoice_number(self) -> str:
        """invoice_number(self) -> str
        Get the invoice invoice_number

        :return: str
        """
        return self.data['number']

    @invoice_number.setter
    @check_error
    def invoice_number(self, invoice_number: str) -> None:
        """invoice_number(self, barcode: str) -> None
        This setter is able to update the invoice number of the item. But the field should already exist.

        :param invoice_number: barcode of the item

        :return: None
        """
        if 'number' not in self.data:
            logging.error(f'{repr(self)}: no number field in the invoice -> not possible to update it')
            self.error = True
        else:
            logging.info(f'{repr(self)}: invoice number changed from "{self.data["number"]}" to "{invoice_number}"')
            self.data['number'] = invoice_number

    def _fetch_data(self) -> Optional[JsonData]:
        """Fetch the json data of the invoice

        :return: :class:`almapiwrapper.record.JsonData` if no error else None
        """

        r = self._api_call('get',
                     f'{self.api_base_url_invoices}/{self.invoice_id}',
                           headers=self._get_headers())
        if r.ok is True:
            # Parse data
            json_data = JsonData(r.json())
            logging.debug(f"{self.__class__.__name__} data fetched")

            return json_data
        else:
            self._handle_error(r, 'unable to fetch invoice data')

    @check_error
    def update(self) -> 'acquisitionslib.Invoice':
        """update(self) -> 'acquisitionslib.Invoice'
        Update the Invoice

        .. note::
            If the record encountered an error, this
            method will be skipped.

        :return: Vendor object
        """

        r = self._api_call('put',
                           f'{self.api_base_url_invoices}/{self.invoice_id}',
                           headers=self._get_headers(),
                           data=bytes(self))

        if r.ok is True:
            self.data = JsonData(r.json())
            logging.info(f'{repr(self)}: Invoice data updated')
        else:
            self._handle_error(r, 'unable to update invoice data')

        return self

    @check_error
    def save(self) -> 'acquisitionslib.Invoice':
        """save(self) -> acquisitionslib.Invoice
        Save a PO Line record in the 'records' folder

        When saved, a suffix is added to the file path with the version.
        Example: records/vendors/vendor_<IZ>_<set_id>_<version>.xml

        :return: object :class:`almapiwrapper.acquisitions.Invoice`

        .. note::
            If the record encountered an error, this
            method will be skipped.
        """
        filepath = f'records/invoices/invoice_{self.zone}_{self.invoice_id}.json'
        self._save_from_path(filepath)
        return self

    @check_error
    def create(self) -> 'acquisitionslib.Invoice':
        """create(self) -> acquisitionslib.Invoice
        Create a Invoice

        :return: Invoice object"""
        r = self._api_call('post',
                           f'{self.api_base_url_invoices}',
                           headers=self._get_headers(),
                           data=bytes(self))

        if r.ok is True:
            self._data = JsonData(r.json())
            self.invoice_id = self.data['id']
            logging.info(f'{repr(self)}: Invoice created: {self.invoice_id}')
        else:
            self._handle_error(r, 'unable to create Invoice')

        return self

    @check_error
    def process_invoice(self) -> 'acquisitionslib.Invoice':
        """process_invoice(self) -> acquisitionslib.Invoice
        Process the invoice

        This operation is useful after adding invoice lines to the invoice

        :return: object :class:`almapiwrapper.acquisitions.Invoice`
        """
        r = self._api_call('post',
                           f'{self.api_base_url_invoices}/{self.invoice_id}/process',
                           headers=self._get_headers(),
                           data='',
                           params={'op': 'process_invoice'})

        if r.ok is True:
            logging.info(f'{repr(self)}: Invoice processed')
        else:
            self._handle_error(r, 'unable to process invoice')

        return self


def fetch_invoices(q: str,
                   zone: str,
                   env: Literal['P', 'S'] = 'P',
                   limit: Optional[int] = None) -> List['Invoice']:
    """fetch_invoices(q: str, zone: str, env: Literal['P', 'S'] = 'P', limit: Optional[int] = None) -> List['Invoices']
    Fetch invoices from a query

    :param q: str : query to fetch the invoices
    :param zone: str : zone of the invoices
    :param env: Literal['P', 'S'] : environment of the entity: 'P' for production and 'S' for sandbox
    :param limit: int : limit of invoices to fetch

    :return: list of invoices
    """
    params = {'q': q}

    if limit is not None:
        params['limit'] = limit

    r = Record._api_call('get',
                         f'{Record.api_base_url}/acq/invoices',
                         headers=Record.build_headers(data_format='json', env=env,
                                                      zone=zone, rights='RW', area='Acquisitions'),
                         params=params)
    if r.ok is True:
        json_data = JsonData(r.json())
        if 'invoice' in json_data.content and json_data.content['invoice'] is not None:
            invoices = [Invoice(invoice['id'], zone=zone, env=env, data=invoice)
                        for invoice in json_data.content['invoice']]
            logging.info(f'fetch_invoices("{q}", "{zone}", "{env}"): '
                         f'{len(invoices)} invoices data available')

            return invoices
        else:
            logging.warning(f'fetch_invoices("{q}", "{zone}", "{env}"): '
                            f'0 invoices data available')
            return []
    else:
        _handle_error(q, r, 'unable to fetch invoices', zone, env)


class InvoiceLine(Record):
    """Class representing an InvoiceLine"""

    api_base_url_invoices: ClassVar[str] = f'{Record.api_base_url}/acq/invoices'

    def __init__(self,
                 invoice_line_id: Optional[str] = None,
                 zone: Optional[str] = None,
                 env: Literal['P', 'S'] = 'P',
                 invoice_number: Optional[str] = None,
                 invoice_id: Optional[str] = None,
                 data: Optional[Union[dict, JsonData]] = None) -> None:
        """Constructor of InvoiceLine Object
        """

        super().__init__(zone, env)
        self.area = 'Acquisitions'
        self.format = 'json'
        self.invoice_line_id = invoice_line_id
        self.invoice_id = invoice_id
        self.invoice_number = invoice_number

        # Invoice id and invoice line id are provided we can directly fetch the data
        if invoice_line_id is not None and invoice_id is not None:
            self._data = self._fetch_data()

        if data is not None:
            self._data = data if type(data) is JsonData else JsonData(data)

        if self.invoice_number is not None:
            invoice = Invoice(invoice_number=self.invoice_number, zone=zone, env=env)
            _ = invoice.data
            if invoice.error is False:
                self.invoice_id = invoice.invoice_id
            else:
                self.error = True
                logging.error(f'No invoice found for invoice_number: {invoice_number}')


        if data is None and (self.invoice_line_id is None or self.invoice_id is None):
            self.error = True
            logging.error('Missing information to construct an InvoiceLine')

    def __repr__(self) -> str:
        """Get a string representation of the object. Useful for logs.

        :return: str representing the object
        """
        return f"{self.__class__.__name__}('{self.invoice_id}', '{self.invoice_line_id}', '{self.zone}', '{self.env}')"


    def _fetch_data(self) -> Optional[JsonData]:
        """Fetch the json data of the invoice

        :return: :class:`almapiwrapper.record.JsonData` if no error else None
        """

        r = self._api_call('get',
                     f'{self.api_base_url_invoices}/{self.invoice_id}/lines/{self.invoice_line_id}',
                           headers=self._get_headers())
        if r.ok is True:
            # Parse data
            json_data = JsonData(r.json())
            logging.debug(f"{self.__class__.__name__} data fetched")

            return json_data
        else:
            self._handle_error(r, 'unable to fetch vendor data')

    @check_error
    def update(self) -> 'acquisitionslib.InvoiceLine':
        """update(self) -> 'acquisitionslib.InvoiceLine'
        Update the InvoiceLine

        .. note::
            If the record encountered an error, this
            method will be skipped.

        :return: Vendor object
        """

        r = self._api_call('put',
                           f'{self.api_base_url_invoices}/{self.invoice_id}/lines/{self.invoice_line_id}',
                           headers=self._get_headers(),
                           data=bytes(self))

        if r.ok is True:
            self.data = JsonData(r.json())
            logging.info(f'{repr(self)}: InvoiceLine data updated')
        else:
            self._handle_error(r, 'unable to update invoice line data')

        return self