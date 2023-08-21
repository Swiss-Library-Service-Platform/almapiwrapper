"""This module allow to create and manage sets in Alma"""
from typing import Literal, Optional, Union, List
import logging
from ..record import XmlData, Record, check_error
from ..inventory import IzBib, NzBib
from ..users import User
from lxml import etree


class RecSet(Record):
    """RecSet(self, set_id: Optional[str] = None, zone: Optional[str] = None, env: Literal['P', 'S'] = 'P', name: Optional[str] = None, data: Optional[XmlData] = None) -> None

    Class representing a set of records

    To get a set it is possible to provide either the set id or the name of the set.

    :param set_id: ID of the set
    :param zone: zone of the set
    :param env: environment of the entity: 'P' for production and 'S' for sandbox
    :param name: name of the set, can be used instead of the set_id
    :param data: :class:`almapiwrapper.record.XmlData` with the data describing the set. If provided, the set_id and name are not required.

    :ivar set_id: initial value: ID of the set
    :ivar zone: initial value: zone of the set
    :ivar env: initial value: environment of the entity: 'P' for production and 'S' for sandbox
    :ivar name: initial value: name of the set
    :ivar data: initial value: data describing the set
    """

    def __new__(cls, *args, **kwargs) -> Union['ItemizedSet', 'LogicalSet', 'RecSet']:
        """Constructor of `RecSet`"""
        if 'data' not in kwargs:
            return super().__new__(cls)
        data = kwargs['data'].content
        if data.find('.//type').text == 'ITEMIZED':
            return super().__new__(ItemizedSet)

        return super().__new__(LogicalSet)

    def __init__(self,
                 set_id: Optional[str] = None,
                 zone: Optional[str] = None,
                 env: Literal['P', 'S'] = 'P',
                 name: Optional[str] = None,
                 data: Optional[XmlData] = None) -> None:
        """Constructor of `RecSet`
        """
        super().__init__(zone, env, data)
        self.area = 'Conf'
        self.format = 'xml'
        self._name = name
        if data is not None and set_id is None:
            set_id = data.content.find('.//id').text
        self._set_id = set_id
        self._members = None

    def _fetch_data(self) -> Optional[XmlData]:
        """This method fetch the data describing the set.

        It is possible to fetch the data of a set by providing the set_id or the name of the set.

        :return: :class:`almapiwrapper.record.XmlData`
        """
        # set_id is not provided. We try to fetch it from the name.
        if self._set_id is None and self._name is not None:
            r = self._api_call('get',
                               f'{self.api_base_url}/conf/sets',
                               params={'q': f'name~{self._name}'},
                               headers=self._get_headers())
            if r.ok is True and XmlData(r.content).content.find('.//set') is not None:
                logging.info(f'{repr(self)}: set data available')
                set_data = XmlData(r.content).content.find('.//set')

                # We store the set_id for fetching the complete data
                self._set_id = set_data.find('.//id').text

            else:
                logging.error(f'{repr(self)}: unable to fetch set data')
                self.error = True
                return None

        # set_id is provided. We fetch the data.
        r = self._api_call('get',
                           f'{self.api_base_url}/conf/sets/{self.set_id}',
                           headers=self._get_headers())
        if r.ok is True:
            logging.info(f'{repr(self)}: set data available')
            return XmlData(r.content)
        else:
            self._handle_error(r, 'unable to fetch set data')

    @property
    def name(self) -> str:
        """Property returning the name of the set.

        :return: str containing set name
        """
        if self._name is None:
            name = self.data.find('.//name')
            if name is not None:
                self._name = name.text

        return self._name

    @property
    def set_id(self) -> str:
        """Property returning the name of the set.

        :return: str containing set name
        """
        if self._set_id is None:
            set_id = self.data.find('.//id')
            if set_id is not None:
                self._set_id = set_id.text

        return self._set_id

    def __repr__(self) -> str:
        """Get a string representation of the object. Useful for logs.

        :return: string
        """
        if self._set_id is not None:
            return f"{self.__class__.__name__}('{self.set_id}', '{self.zone}', '{self.env}')"
        else:
            return f"{self.__class__.__name__}(name='{self.name}', zone='{self.zone}', env='{self.env}')"

    @check_error
    def save(self) -> Union['RecSet', 'ItemizedSet', 'LogicalSet']:
        """save() -> Union['RecSet', 'ItemizedSet', 'LogicalSet']
        Save a set record in the 'records' folder

        When saved, a suffix is added to the file path with the version.
        Example: records/set_<IZ>_<set_id>_<version>.xml

        :return: object :class:`almapiwrapper.users.Fee`

        .. note::
            If the record encountered an error, this
            method will be skipped.
        """
        filepath = f'records/recset/set_{self.zone}_{self.name}.xml'
        self._save_from_path(filepath)
        return self

    @check_error
    def get_members_number(self) -> int:
        """get_members_number() -> int
        Return the number of members

        :return: int with the number of records

        .. note::
            If the record encountered an error, this
            method will be skipped.
        """
        # If number of records is not provided, it's a new set and data need to be refreshed
        if self.data.find('.//number_of_members') is None:
            self.data = self._fetch_data()
        return int(self.data.find('.//number_of_members').text)

    @check_error
    def get_set_type(self) -> str:
        """get_set_type() -> str
        Return the type of the set

        :return: str indicating the type of the set

        .. note::
            If the record encountered an error, this
            method will be skipped.
        """
        return self.data.find('.//type').text

    @check_error
    def get_content_type(self) -> str:
        """get_content_type() -> str
        Return the type of the set

        :return: str indicating the type of the set

        .. note::
            If the record encountered an error, this
            method will be skipped.
        """
        return self.data.find('.//content').text

    @check_error
    def update(self) -> Union['RecSet', 'ItemizedSet', 'LogicalSet']:
        """update() -> Union['RecSet', 'ItemizedSet', 'LogicalSet']
        Update set data.

        :return: the updated set object

        .. note::
            If the record encountered an error, this
            method will be skipped.
        """
        r = self._api_call('put',
                           f'{self.api_base_url}/conf/sets/{self.set_id}',
                           headers=self._get_headers(),
                           data=bytes(self))

        if r.ok is True:
            self.data = XmlData(r.content)
            logging.info(f'{repr(self)}: set data updated')
        else:
            self._handle_error(r, 'unable to update set data')

        return self


    @check_error
    def delete(self) -> None:
        """delete() -> None
        Delete a set

        :return: None

        .. note::
            If the record encountered an error, this
            method will be skipped.
        """

        r = self._api_call('delete',
                           f'{self.api_base_url}/conf/sets/{self.set_id}',
                           headers=self._get_headers())
        if r.ok is True:
            logging.info(f'{repr(self)}: set deleted')
            return
        else:
            print(r.text)
            self._handle_error(r, f'unable to delete the set')

    @check_error
    def get_members(self) -> list[Record]:
        """get_members() -> list[Record]
        Return a list with all the records of the set

        :return: list of records depending on the type of the set

        .. note::
            If the record encountered an error, this
            method will be skipped.
        """

        # Prevent to fetch data twice, if already available
        if self._members is not None:
            members = self._members
            return members
        else:
            self._members = []
            while len(self._members) < self.get_members_number():
                r = self._api_call('get',
                                   f'{self.api_base_url}/conf/sets/{self.set_id}/members',
                                   params={'limit': '100', 'offset': str(len(self._members))},
                                   headers=self._get_headers())
                if r.ok is False:
                    self._handle_error(r, f'{repr(self)}: unable to fetch set members')
                    return self._members
                else:
                    rec_ids = [rec_id.text for rec_id in XmlData(r.content).content.findall('.//member/id')]

                    # Build members -> IZ mms_id
                    if self.get_content_type() in ['BIB_MMS', 'IEP'] and self.zone != 'NZ':
                        self._members += [IzBib(rec_id, self.zone, self.env) for rec_id in rec_ids]

                    # Build members -> IZ mms_id
                    elif self.get_content_type() in ['BIB_MMS'] and self.zone == 'NZ':
                        self._members += [NzBib(rec_id, self.env) for rec_id in rec_ids]

                    # Build members -> users
                    elif self.get_content_type() == 'USER':
                        self._members += [User(rec_id, self.zone, self.env) for rec_id in rec_ids]

                    # Type of content not integrated
                    else:
                        self._members += rec_ids
                        logging.warning(f'{repr(self)}: "{self.get_content_type()}" not integrated, only id are returned.')

                    logging.info(f'{repr(self)}: {len(self._members)} / {self.get_members_number()} members fetched')

            return self._members


class LogicalSet(RecSet):
    """LogicalSet(set_id: Optional[str] = None, zone: Optional[str] = None, env: Literal['P', 'S'] = 'P', name: Optional[str] = None, data: Optional[XmlData] = None) -> None

    Class representing a logical set of records

    :param set_id: ID of the set
    :param zone: zone of the set
    :param env: environment of the entity: 'P' for production and 'S' for sandbox
    :param name: name of the set, can be used instead of the set_id
    :param data: :class:`almapiwrapper.record.XmlData` with the data describing the set. If provided, the set_id and name are not required.


    :ivar set_id: initial value: ID of the set
    :ivar zone: initial value: zone of the set
    :ivar env: initial value: environment of the entity: 'P' for production and 'S' for sandbox
    :ivar name: initial value: name of the set
    :ivar data: initial value: data describing the set
    """

    def __new__(cls, *args, **kwargs):
        return object.__new__(cls)

class ItemizedSet(RecSet):
    """ItemizedSet(set_id: Optional[str] = None, zone: Optional[str] = None, env: Literal['P', 'S'] = 'P', name: Optional[str] = None, data: Optional[XmlData] = None) -> None

    Class representing an itemized set of records

    :param set_id: ID of the set
    :param zone: zone of the set
    :param env: environment of the entity: 'P' for production and 'S' for sandbox
    :param name: name of the set, can be used instead of the set_id
    :param data: :class:`almapiwrapper.record.XmlData` with the data describing the set. If provided, the set_id and name are not required.

    :ivar set_id: initial value: ID of the set
    :ivar zone: initial value: zone of the set
    :ivar env: initial value: environment of the entity: 'P' for production and 'S' for sandbox
    :ivar name: initial value: name of the set
    :ivar data: initial value: data describing the set
    """
    def __new__(cls, *args, **kwargs):
        return object.__new__(cls)

    @check_error
    def add_members(self,
                    record_ids: List[str],
                    fail_on_invalid_id: Optional[bool] = True) -> 'ItemizedSet':
        """add_members(record_ids: List[str], fail_on_invalid_id: Optional[bool] = True) -> 'ItemizedSet'
        Add members to a set

        :param record_ids: list of record ids to add to the set
        :param fail_on_invalid_id: if True, raise an error if one of the record id is invalid
        :return: `ItemizedSet` object

        .. note::
            If the record encountered an error, this
            method will be skipped.
        """
        # params of the add members API call
        params = {'op': 'add_members',
                  'fail_on_invalid_id': fail_on_invalid_id}

        # Split the list of record ids in chunks of 1000
        for i in range(len(record_ids) // 1000 + 1):

            # Remove the members node if existing, useful when more than 1000 members
            old_members = self.data.find('members')
            if old_members is not None:
                self.data.remove(old_members)

            members = etree.Element('members')
            for record_id in record_ids[i*1000:(i+1)*1000]:
                etree.SubElement(etree.SubElement(members, 'member'), 'id').text = record_id

            self.data.append(members)

            number_of_members_before_update = self.get_members_number()

            r = self._api_call('post',
                               f'{self.api_base_url}/conf/sets/{self.set_id}',
                               headers=self._get_headers(),
                               params=params,
                               data=bytes(self))

            if r.ok is True:
                self.data = XmlData(r.content)
                number_of_members_after_update = self.get_members_number()
                self._members = None
                logging.info(f'{repr(self)}: adding members succeeded, '
                             f'{number_of_members_after_update - number_of_members_before_update} members added '
                             f'({number_of_members_after_update} members in total)')
            else:
                self._handle_error(r, 'unable to add members to the set')
                break

        return self

class NewLogicalSet(RecSet):
    """NewLogicalSet(zone: str, env: Literal['P', 'S'] = 'P', name: Optional[str] = None, description: Optional[str] = None, query: Optional[str] = None, created_by: Optional[str] = None, private: Optional[bool] = False, data: Optional[XmlData] = None) -> None
    Class representing a new logical set of records

    To create a new set, it is possible to provide directly the XML data or
    to give all the required parameters.

    :param name: name of the set
    :param zone: zone of the set
    :param env: environment of the set: 'P' for production and 'S' for sandbox
    :param description: description of the set
    :param query: query to build the set
    :param created_by: user who created the set
    :param private: set as private or not
    :param data: :class:`almapiwrapper.record.XmlData` object, can be used instead of the XML data of the set

    :ivar zone: initial value: zone of the set
    :ivar env: initial value: environment of the set: 'P' for production and 'S' for sandbox
    :ivar data: initial value: :class:`almapiwrapper.record.XmlData`
    :ivar area: initial value: area of the set: will be "Conf"
    :ivar format: initial value: data format of the set: will be "xml"
    """

    def __new__(cls, *args, **kwargs):
        return object.__new__(cls)
    def __init__(self,
                 zone: str,
                 env: Literal['P', 'S'] = 'P',
                 name: Optional[str] = None,
                 description: Optional[str] = None,
                 query: Optional[str] = None,
                 created_by: Optional[str] = None,
                 private: Optional[bool] = False,
                 data: Optional[XmlData] = None) -> None:
        """
        Constructor of `NewLogicalSet`
        """
        super(RecSet, self).__init__(zone, env, data)
        self.area = 'Conf'
        self.format = 'xml'
        if self._data is None and name is not None and query is not None and created_by is not None:
            self._data = self._create_data(name, query, description, created_by, private)
        if self._data is None:
            logging.error('NewLogicalSet: missing parameters to create a new set')

    def __repr__(self) -> str:
        """Get a string representation of the object. Useful for logs.

        :return: string
        """
        return f"{self.__class__.__name__}('{self.zone}', '{self.env}', '{self.data.find('name').text}', " \
               f"'{self.data.find('description').text}', '{self.data.find('query').text}', " \
               f"'{self.data.find('created_by').text}', {self.data.find('private').text=='true'})"

    @staticmethod
    def _create_data(name, query, description, created_by, private) -> XmlData:
        """Create the XML data for a new set

        :param name: name of the set
        :param query: query of the set
        :param description: description of the set
        :param created_by: user who created the set
        :param private: bool indicating if set is private or public
        :return: XML data
        """
        content = query.split()[0]
        root = etree.Element('set')
        etree.SubElement(root, 'name').text = name
        etree.SubElement(root, 'type').text = 'LOGICAL'
        etree.SubElement(root, 'content').text = content
        etree.SubElement(root, 'description').text = description
        etree.SubElement(root, 'query').text = query
        etree.SubElement(root, 'created_by').text = created_by
        etree.SubElement(root, 'private').text = str(private).lower()
        return XmlData(etree.tostring(root))

    @check_error
    def create(self) -> Union['LogicalSet', 'NewLogicalSet']:
        """create() -> Union['LogicalSet', 'NewLogicalSet']
        Create the logical set

        :return: `almapiwrapper.config.LogicalSet` or `almapiwrapper.config.NewLogicalSet` in case of error

        .. note::
            If the record encountered an error, this
            method will be skipped.
        """
        r = self._api_call('post',
                           f'{self.api_base_url}/conf/sets',
                           headers=self._get_headers(),
                           data=bytes(self))
        if r.ok is True:
            self._data = XmlData(r.content)
            set_id = self.data.find('.//id').text
            new_rec = RecSet(set_id, self.zone, self.env, data=self._data)
            logging.info(f'{repr(new_rec)}: set created')
            return new_rec
        else:
            self._handle_error(r, f'unable to create the set')
            return self


class NewItemizedSet(RecSet):
    """NewItemizedSet(zone: str, env: Literal['P', 'S'] = 'P', name: Optional[str] = None, content: Optional[str] = None, description: Optional[str] = None, private: Optional[bool] = False, members: Optional[List[str]] = None, from_logical_set: Optional[Union[str, `LogicalSet`]] = None, data: Optional[XmlData] = None) -> None
    Class representing a new itemized set of records

    To create a new set, it is possible to provide directly the XML data or
    to give all the required parameters.

    :param zone: zone of the set
    :param env: environment of the set: 'P' for production and 'S' for sandbox
    :param name: name of the set
    :param description: description of the set
    :param query: query to build the set
    :param private: set as private or not
    :param members: list of members of the set, must be a list of primary ids
    :param from_logical_set: set_id or :class:`almapiwrapper.config.LogicalSet` object to create the set from
    :param data: :class:`almapiwrapper.record.XmlData` object, can be used instead of the XML data of the set

    :ivar zone: initial value: zone of the set
    :ivar env: initial value: environment of the set: 'P' for production and 'S' for sandbox
    :ivar data: initial value: :class:`almapiwrapper.record.XmlData`
    :ivar from_logical_set: initial value: set_id string of `LogicalSet` to create the `ItemizedSet` from
    :ivar area: initial value: area of the set: will be "Conf"
    :ivar members: initial value: list of members of the set, must be a list of primary ids
    :ivar format: initial value: data format of the set: will be "xml"
    """

    def __new__(cls, *args, **kwargs):
        return object.__new__(cls)
    def __init__(self,
                 zone: str,
                 env: Literal['P', 'S'] = 'P',
                 name: Optional[str] = None,
                 content: Optional[str] = None,
                 description: Optional[str] = None,
                 private: Optional[bool] = False,
                 members: Optional[List[str]] = None,
                 from_logical_set: Optional[Union[str, RecSet]] = None,
                 data: Optional[XmlData] = None) -> None:
        """Constructor of `NewItemizedSet`
        """
        super(RecSet, self).__init__(zone, env, data)
        self.area = 'Conf'
        self.format = 'xml'
        self.members = members

        # Will be None if itemized set is not created from a logical set. Set can be indicated by its ID or by a RecSet
        self.from_logical_set = from_logical_set.set_id if isinstance(from_logical_set, LogicalSet) is True or \
            isinstance(from_logical_set, RecSet) is True else from_logical_set

        # If itemized set is created from a logical set, we can get the name and the content from the logical set
        if  self.from_logical_set is not None and (name is None or content is None):
            if isinstance(from_logical_set, str) is True:
                from_logical_set = LogicalSetSet(from_logical_set, zone, env)
            if name is None:
                name = from_logical_set.data.find('name').text + '_itemized'
            if content is None:
                content = from_logical_set.data.find('content').text

        # Check if required parameters are provided
        if self._data is None and name is not None and content is not None:
            self._data = self._create_data(name, content, description, private, self.from_logical_set)
        else:
            logging.error('NewLogicalSet: missing parameters to create a new set')

    @staticmethod
    def _create_data(name: str,
                     content: str,
                     description: Optional[str] = None,
                     private: Optional[bool] = False,
                     from_logical_set: Optional[str] = None) -> XmlData:
        """Create the XML data for a new set

        :param name: name of the set
        :param content: content of the set
        :param description: description of the set
        :param private: bool indicating if set is private or public
        :return: :class:`almapiwrapper.record.XmlData` object

        """
        root = etree.Element('set')
        etree.SubElement(root, 'name').text = name
        etree.SubElement(root, 'type').text = 'ITEMIZED'
        etree.SubElement(root, 'content').text = content
        etree.SubElement(root, 'description').text = description if description is not None else ''
        etree.SubElement(root, 'private').text = str(private).lower()
        if from_logical_set is not None:
            etree.SubElement(root, 'fromLogicalSet').text = from_logical_set
        return XmlData(etree.tostring(root))

    def __repr__(self) -> str:
        """Get a string representation of the object. Useful for logs.

        :return: string
        """
        return f"{self.__class__.__name__}('{self.zone}', '{self.env}', '{self.data.find('name').text}', " \
               f"'{self.data.find('content').text}', " \
               f"'{self.data.find('description').text if self.data.find('description').text is not None else ''}', " \
               f"{self.data.find('private').text == 'true'})"

    @check_error
    def create(self) -> Union['ItemizedSet', 'NewItemizedSet'] :
        """create() -> Union['LogicalSet', 'NewLogicalSet']
        Create the itemized set

        :return: `almapiwrapper.config.ItemizedSet` or `almapiwrapper.config.NewItemizedSet` in case of error

        .. note::
            If the record encountered an error, this
            method will be skipped.
        """
        params = {'from_logical_set': self.from_logical_set} if self.from_logical_set is not None else {}

        r = self._api_call('post',
                           f'{self.api_base_url}/conf/sets',
                           headers=self._get_headers(),
                           params=params,
                           data=bytes(self))
        if r.ok is True:
            logging.info(f'{repr(self)}: set created')
            self._data = XmlData(r.content)
            set_id = self.data.find('.//id').text
            new_rec = RecSet(set_id, self.zone, self.env, data=self._data)
            logging.info(f'{repr(new_rec)}: set created')
            if self.members is not None:
                new_rec.add_members(self.members)
            return new_rec
        else:
            self._handle_error(r, f'unable to create the set')
            return self
