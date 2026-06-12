"""Module for managing Alma integration profiles via the Alma API."""
from typing import Optional, List, Dict, Union, Literal
import logging
import requests
from almapiwrapper.record import JsonData, Record, check_error

def fetch_integration_profiles(zone: str, env: Optional[Literal['P', 'S']] = 'P') -> List['IntegrationProfile']:
    """Fetch the list of Alma integration profiles.

    :param zone: institutional zone
    :param env: environment ('P' for production, 'S' for sandbox)
    :return: list of IntegrationProfile objects
    """
    profiles = []
    r = requests.get(f'{IntegrationProfile.api_base_url}/conf/integration-profiles',
                     params={'limit': '100'},
                     headers=Record.build_headers(data_format='json', env=env, zone=zone, rights='RW', area='Conf'))
    if r.ok and 'integration_profile' in r.json():
        profiles_list = JsonData(r.json())
        profiles = [IntegrationProfile(zone=zone, env=env, data=profile_data)
                    for profile_data in profiles_list.content['integration_profile']]
    elif r.ok:
        _handle_error(r, 'no integration profile available', zone, env)
    else:
        _handle_error(r, 'unable to fetch integration profiles', zone, env)
    return profiles

def _handle_error(r: requests.models.Response, msg: str, zone: str, env: Optional[Literal['P', 'S']] = 'P') -> None:
    """Error handling and logging for API calls."""
    try:
        json_data = r.json()
        error_message = json_data['errorList']['error'][0]['errorMessage']
    except Exception:
        error_message = str(r.text)
    logging.error(f'fetch_integration_profiles({zone}, {env}) - {r.status_code}: {msg} / {error_message}')

class IntegrationProfile(Record):
    """Class representing an Alma integration profile."""
    def __init__(self,
                 profile_id: Optional[str] = None,
                 zone: Optional[str] = None,
                 env: Optional[Literal['P', 'S']] = 'P',
                 data: Optional[Union[Dict, JsonData, str]] = None) -> None:
        """Constructor for IntegrationProfile.
        :param zone: institutional zone
        :param env: environment ('P' for production, 'S' for sandbox)
        :param profile_id: profile identifier
        :param data: profile data (JsonData or dict)
        """
        super().__init__(zone, env, data)
        self.area = 'Conf'
        self.format = 'json'
        self.profile_id = profile_id or (data['id'] if data and 'id' in data else None)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}('{self.zone}', '{self.profile_id}', '{self.env}')"

    def _fetch_data(self) -> Optional[JsonData]:
        """Fetch the integration profile data."""
        if not self.profile_id:
            logging.error(f'{repr(self)}: missing profile_id for fetch')
            return None
        r = self.api_call('get',
                          f'{self.api_base_url}/conf/integration-profiles/{self.profile_id}',
                          headers=self._get_headers())
        if r.ok:
            logging.info(f'{repr(self)}: profile data available')
            return JsonData(r.json())
        else:
            self._handle_error(r, 'unable to fetch integration profile')
        return None

    @check_error
    def create(self) -> 'IntegrationProfile':
        """Create a new integration profile."""
        r = self.api_call('post',
                          f'{self.api_base_url}/conf/integration-profiles',
                          headers=self._get_headers(),
                          data=bytes(self))
        if r.ok:
            logging.info(f'{repr(self)}: new profile created')
            self.profile_id = r.json().get('id')
            self._data = JsonData(r.json())
        else:
            self._handle_error(r, 'unable to create integration profile')
        return self

    @check_error
    def update(self) -> 'IntegrationProfile':
        """Update the integration profile."""
        if not self.profile_id:
            logging.error(f'{repr(self)}: missing profile_id for update')
            return self
        r = self.api_call('put',
                          f'{self.api_base_url}/conf/integration-profiles/{self.profile_id}',
                          headers=self._get_headers(),
                          data=bytes(self))
        if r.ok:
            logging.info(f'{repr(self)}: profile updated')
            self._data = JsonData(r.json())
        else:
            self._handle_error(r, 'unable to update integration profile')
        return self

    @check_error
    def delete(self) -> None:
        """Delete the integration profile."""
        if not self.profile_id:
            logging.error(f'{repr(self)}: missing profile_id for delete')
            return None
        r = self.api_call('delete',
                          f'{self.api_base_url}/conf/integration-profiles/{self.profile_id}',
                          headers=self._get_headers())
        if r.ok:
            logging.info(f'{repr(self)}: profile deleted')
        else:
            self._handle_error(r, 'unable to delete integration profile')
        return None
