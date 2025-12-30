"""This module allow to create and manage sets in Alma"""
from typing import Literal, Optional, Dict, Union
import logging
from ..record import XmlData, JsonData, Record, check_error


class Job(Record):
    """
    Represents an Alma job and provides access to its execution instances.

    This class allows you to:
    - list job execution instances,
    - retrieve detailed information about a specific instance,
    - monitor the execution state of an instance.

    :param job_id: Alma job identifier.
    :type job_id: str
    :param zone: Job zone (e.g. ``NZ``).
    :type zone: str
    :param env: Entity environment:
                ``'P'`` for production,
                ``'S'`` for sandbox.
    :type env: str
    :param job_type: Job type:
                     ``'M'`` for manual,
                     ``'S'`` for scheduled.
    :type job_type: str

    :ivar job_id: Job identifier.
    :ivar zone: Job zone.
    :ivar env: Environment (``'P'`` or ``'S'``).
    :ivar job_type: Job type (``'M'`` or ``'S'``).
    :ivar instance_id: Current instance identifier.
    :ivar area: API area is ``'Conf'``.
    :ivar format: API response format (default: ``'xml'``).

    **Example**

    Example showing how to query a job and monitor an execution instance:

    .. code-block:: python

        from almapiwrapper.config import Job
        from almapiwrapper.configlog import config_log

        # Initialize logging
        config_log()

        # Create the job
        job = Job(job_id="135", zone="NZ")

        # Retrieve all job instances
        instances = job.get_instances()
        print(instances)

        # Retrieve detailed information for a specific instance
        instance_id = "55493478870005501"
        instance = job.get_instance_info(instance_id)
        print(instance)

        # Access counters returned by the job
        counters = instance.content["counter"]
        print(counters)

        # Check execution state of the instance
        state = job.check_instance_state(instance_id)
        print(state)
    """
    def __init__(self,
                 job_id: str,
                 zone: str,
                 env: Literal['P', 'S'] = 'P',
                 job_type: Literal['M', 'S', 'O'] = 'M') -> None:
        """Constructor of `Job`
        """
        super().__init__(zone, env)
        self.area = 'Conf'
        self.format = 'xml'
        self.job_id = job_id
        self.job_type = job_type
        self.instance_id = None

    def _fetch_data(self) -> Optional[XmlData]:
        """This method fetch the data describing the job.

        :return: :class:`almapiwrapper.record.XmlData`
        """
        r = self._api_call('get',
                           f'{self.api_base_url}/conf/jobs/{self.job_type}{self.job_id}',
                           headers=self._get_headers())
        if r.ok:
            logging.info(f'{repr(self)}: job data available')
            return XmlData(r.content)
        else:
            self._handle_error(r, 'unable to fetch job data')
            return None

    def __repr__(self) -> str:
        """Get a string representation of the object. Useful for logs.

        :return: string
        """
        return f"{self.__class__.__name__}('{self.job_id}', '{self.zone}', '{self.env}')"

    @check_error
    def run(self, parameters: Optional[Union[str, 'XmlData']] = '<job/>') -> Optional['XmlData']:
        """run(parameters: Optional[Union[str, 'XmlData']] = '<job/>') -> Optional['XmlData']
        Run the job with the provided parameters

        :param parameters: :class:`almapiwrapper.record.XmlData` or string with the parameters to use for the job.
            For some jobs no parameters are required.

        :return: :class:`almapiwrapper.record.XmlData` with the instance of the job or None in case of error.

        .. note::
            If the record encountered an error, this
            method will be skipped.
        """

        # Transform the XmlData parameters to string, useful to make the api request
        if type(parameters) == XmlData:
            parameters = str(parameters)

        r = self._api_call('post',
                           f'{self.api_base_url}/conf/jobs/{self.job_type}{self.job_id}',
                           params={'op': 'run'},
                           data=parameters,
                           headers=self._get_headers())

        if r.ok:
            result = XmlData(r.content)

            # Fetch the instance ID
            link = result.content.find('.//additional_info').get('link')
            instance_id = link.split('/')[-1]
            logging.info(f'{repr(self)}: run job successful, instance: {instance_id}')

            # Store the current instance ID in the instance_id attribute of the job
            self.instance_id = instance_id
            return result
        else:
            self._handle_error(r, 'unable to run the job')
            return None

    @check_error
    def get_instance_info(self, instance_id: Optional[str] = None) -> Optional['JsonData']:
        """get_instance_info(instance_id: Optional[str] = None) -> Optional['JsonData']
        Get information about a specif job instance

        :param instance_id: optional parameter indicating the instance to check. If not
            provided it will use the instance id of a job started

        :return: :class:`almapiwrapper.record.JsonData` with the details of a job instance
            return None in case of error

        .. note::
            If the record encountered an error, this
            method will be skipped.
        """
        if instance_id is None:
            instance_id = self.instance_id

        if instance_id is None:
            logging.error(f'{repr(self)}: No instance job ID available or provided')
            return None

        r = self._api_call('get',
                           f'{self.api_base_url}/conf/jobs/{self.job_type}{self.job_id}/instances/{instance_id}',
                           headers=self._get_headers(data_format='json'))
        if r.ok:
            logging.info(f'{repr(self)}: job information available for instance {instance_id}')
            return JsonData(r.json())
        else:
            self._handle_error(r, 'unable to fetch job data')
            return None

    @check_error
    def check_instance_state(self, instance_id: Optional[str] = None) -> Optional[Dict]:
        """check_instance_state(instance_id: Optional[str] = None) -> Optional[Dict]
        Check the state of the provided instance id or of instance started
        with :meth:`almapiwrapper.config.Job.run`

        :param instance_id: optional parameter indicating the instance to check. If not
            provided it will use the instance id of a job started

        .. note::
            If the record encountered an error, this
            method will be skipped.
        """
        data = self.get_instance_info(instance_id)

        if data is not None:
            return {'status': data.content['status']['value'],
                    'progress': data.content['progress']}
        return None

    @check_error
    def get_instances(self) -> Optional['JsonData']:
        """get_instances(self) -> Optional['JsonData']
        Get the list of the instances of a job in json format

        :return: :class:`almapiwrapper.record.JsonData` with the list of job instances
            return None in case of error

        .. note::
            If the record encountered an error, this
            method will be skipped.
        """
        r = self._api_call('get',
                           f'{self.api_base_url}/conf/jobs/{self.job_type}{self.job_id}/instances',
                           headers=self._get_headers(data_format='json'))
        if r.ok:
            logging.info(f'{repr(self)}: job information available for instances')
            return JsonData(r.json())
        else:
            self._handle_error(r, 'unable to fetch job data')
            return None
