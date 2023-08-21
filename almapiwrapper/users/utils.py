import almapiwrapper.users as userslib
from typing import List, Optional, Literal, Union
from ..apikeys import ApiKeys
from ..record import Record, JsonData
import requests
import logging
import time
from copy import deepcopy
import re
from json import JSONDecodeError
from lxml import etree


def fetch_users(q: str, zone: str, env: Optional[Literal['P', 'S']] = 'P') -> List[userslib.User]:
    """Search users in IZ according to a request

    :param q: request in API syntax. "user_group~06" will search every linked account
    :param zone: code of the IZ, NZ or "all" for all IZs NZ excepted.
    :param env: "P" for production, "S" for sandbox. Default is production
    :return: list of :class:`almapiwrapper.users.User`
    """
    error = False
    users = []
    list_iz = ApiKeys().get_iz_codes() if zone == 'all' else [zone]
    for z in list_iz:

        # Interrupt in case of any error
        if error is True:
            break

        # Init counters
        offset = 0
        nb_total_records = 0

        # Handle offset if more than 100 results are available
        while offset == 0 or offset < nb_total_records:

            # Make request
            r = requests.get(f'{userslib.User.api_base_url}',
                             params={'q': q, 'limit': 100, 'offset': offset},
                             headers=Record.build_headers(data_format='json', env=env,
                                                          zone=z, rights='RW', area='Users'))

            # Check result
            if r.ok is True:
                users_list = JsonData(r.json())
                nb_total_records = int(users_list.content['total_record_count'])

                if 'user' in users_list.content and users_list.content['user'] is not None:
                    users += [userslib.User(user['primary_id'], z, env) for user in users_list.content['user']]
                    nb_users = len(users_list.content['user'])
                else:
                    nb_users = 0

                logging.info(f'fetch_users("{q}", "{z}", "{env}"): '
                             f'{offset + nb_users} / '
                             f'{nb_total_records} users data available')
                offset += 100
            else:
                _handle_error(q, r, f'unable to fetch data', z, env)
                error = True
                break

    return users


def fetch_user_in_all_iz(primary_id: str, env: Optional[Literal['P', 'S']] = 'P') -> List[userslib.User]:
    """Fetch by primary ID a user in all IZ

    :param primary_id: primary ID of the user to search across all IZs
    :param env: "P" for production, "S" for sandbox. Default is production
    :return: list of :class:`almapiwrapper.users.User`
    """

    list_iz = ApiKeys().get_iz_codes(env=env)
    users = []
    for iz in list_iz:
        users_temp = fetch_users(f'primary_id~{primary_id.replace(" ", "+")}', iz, env)
        if len(users_temp) == 1:
            users += users_temp

    return users


def check_synchro(nz_users: Union[List[userslib.User], userslib.User]) -> Optional[List[userslib.User]]:
    """Test if a NZ user is synchronized with copies of the account across IZs.
    :param nz_users: list of :class:`almapiwrapper.users.User` or only one :class:`almapiwrapper.users.User`
    :return: list of :class:`almapiwrapper.users.User` with not synchronized IZ user accounts
    """

    not_synchro_iz_users = []
    if type(nz_users) is not list:
        nz_users = [nz_users]

    nb_users = len(nz_users)
    nz_users = [user for user in nz_users if user.zone == 'NZ']

    if len(nz_users) < nb_users:
        logging.error(f'Impossible to check synchronization on not NZ account')
        return None

    for nz_user in nz_users:
        nz_user.add_synchro_note()

    time.sleep(300)

    for nz_user in nz_users:
        nz_user.save()
        iz_users = fetch_user_in_all_iz(nz_user.primary_id, nz_user.env)

        for iz_user in iz_users:
            iz_user.save()
            if iz_user.check_synchro_note() is False:
                not_synchro_iz_users.append(iz_user)

    for nz_user in nz_users:
        nz_user.remove_synchro_note()

    if len(not_synchro_iz_users) > 0:
        logging.warning(f'Count of not synchronized users: {len(not_synchro_iz_users)}')
    else:
        logging.info(f'Count of not synchronized users: {len(not_synchro_iz_users)}')

    return not_synchro_iz_users

def force_synchro(nz_users: Union[List[userslib.User], userslib.User]) -> List[str]:
    """Force synchronization of a NZ user with copies of the account across IZs.
    :param nz_users: list of :class:`almapiwrapper.users.User` or only one :class:`almapiwrapper.users.User`
    :return: list of errors
    """

    error_msg = []

    if type(nz_users) is not list:
        nz_users = [nz_users]

    nb_users = len(nz_users)
    nz_users = [user for user in nz_users if user.zone == 'NZ']

    if len(nz_users) < nb_users:
        logging.error(f'Impossible to force synchronization on not NZ account')
        error_msg.append(f'Impossible to force synchronization on not NZ account')
        return error_msg

    for nz_user in nz_users:
        _ = nz_user.data
        if nz_user.error is True:
            error_msg.append(f'{repr(nz_user)}: no NZ account -> impossible to force synchronization')
            logging.error(f'{repr(nz_user)}: no NZ account -> impossible to force synchronization')

            continue
        iz_users = fetch_user_in_all_iz(nz_user.primary_id, nz_user.env)
        _ = iz_users

        for iz_user in iz_users:
            iz_user.save()

            # Copy contact_info
            iz_user.data['contact_info'] = deepcopy(nz_user.data['contact_info'])

            # Copy identifiers
            nz_ids = [nz_id['value'] for nz_id in nz_user.data['user_identifier']]
            local_ids = [u_id for u_id in iz_user.data['user_identifier'] if
                         u_id['value'] not in nz_ids and u_id['id_type']['value'] == '03']
            iz_user.data['user_identifier'] = local_ids + nz_user.data['user_identifier']
    
            # Copy notes
            local_notes = [u_note for u_note in iz_user.data['user_note'] if u_note['segment_type'] == 'Internal']
            iz_user.data['user_note'] = local_notes + nz_user.data['user_note']
    
            # Copy user_group
            nz_user_group = nz_user.data['user_group']['value']
            local_user_group = iz_user.data['user_group']['value']
            if local_user_group == '':
                iz_user.data['user_group']['value'] = nz_user_group
            elif re.match(r'\d{2}', nz_user_group):
                if re.match(r'\d{2}', local_user_group):
                    iz_user.data['user_group']['value'] = nz_user_group
            else:
                if re.match(r'\d{2}', local_user_group):
                    iz_user.data['user_group']['value'] = nz_user_group
            iz_user.update(override=['user_group'])
            if iz_user.error is True:
                error_msg.append(f'{repr(iz_user)}: error on update / {iz_user.error_msg}')

    return error_msg

def _handle_error(q: str, r: requests.models.Response, msg: str, zone: str, env: str):
    """Set the record error attribute to True and write the logs about the error

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

    logging.error(f'fetch_users("{q}", "{zone}", "{env}") - {r.status_code}: '
                  f'{msg} / {error_message}')


if __name__ == "__main__":
    pass
