import json
from collections import namedtuple
from datetime import datetime
from typing import List

import tzlocal

from sapio.utils.data_type_models import C_OutboundCommunicationConfigModel
from sapio.utils.record_util import RecordUtil


def custom_decoder(pojo_name, obj_dict):
    return namedtuple(pojo_name, obj_dict.keys())(*obj_dict.values())


def json_to_pojo(json_data, pojo_class):
    try:
        response_dict = json.loads(json_data)
        # Replace hyphens with underscores in keys
        response_dict = {key.replace('-', '_'): value for key, value in response_dict.items()}
        return pojo_class(**response_dict)
    except Exception as e:
        raise e


def get_outbound_comm_config(config_id, context):
    if not config_id:
        raise Exception(f"Error: ConfigId is missing to query config records'")
    configs: List[C_OutboundCommunicationConfigModel] = RecordUtil(context).query_models(
        C_OutboundCommunicationConfigModel,
        C_OutboundCommunicationConfigModel.C_CONFIGID__FIELD_NAME.field_name,
        [config_id])
    if len(configs) == 0:
        raise Exception(f"Error: No Outbound Communication config found with the ID '{config_id}'")
    return configs[0]


def convert_to_hl7_timestamp(timestamp, precision='second'):
    if not timestamp:
        return ""
    # Convert the timestamp to a datetime object
    local_tz = tzlocal.get_localzone()
    dt = datetime.fromtimestamp(timestamp/1000, tz=local_tz)

    # Format the datetime object based on the degree of precision
    if precision == 'year':
        hl7_timestamp = dt.strftime('%Y')
    elif precision == 'month':
        hl7_timestamp = dt.strftime('%Y%m')
    elif precision == 'day':
        hl7_timestamp = dt.strftime('%Y%m%d')
    elif precision == 'hour':
        hl7_timestamp = dt.strftime('%Y%m%d%H')
    elif precision == 'minute':
        hl7_timestamp = dt.strftime('%Y%m%d%H%M')
    elif precision == 'second':
        hl7_timestamp = dt.strftime('%Y%m%d%H%M%S')
    else:
        hl7_timestamp = dt.strftime('%Y%m%d%H%M%S.%f')[:-3]
    return hl7_timestamp
