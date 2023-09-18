# -*- coding = utf-8 -*-
# @Time:2023/9/12,16:34
# @Author:邓云龙
# @File:GP.py
# @Software:PyCharm

import os
import re
import copy
import datetime
import numpy as np
import time
import pandas as pd
from pandas import ExcelWriter
import threading  # 线程模块
from multiprocessing import Process  # 进程模块
import subprocess

features = ["CCSDS_OMM_VERS", "COMMENT", "CREATION_DATE", "ORIGINATOR",
            "OBJECT_NAME", "OBJECT_ID",
            "CENTER_NAME", "REF_FRAME", "TIME_SYSTEM", "MEAN_ELEMENT_THEORY",
            "EPOCH", "MEAN_MOTION", "ECCENTRICITY", "INCLINATION",
            "RA_OF_ASC_NODE", "ARG_OF_PERICENTER", "MEAN_ANOMALY",
            "EPHEMERIS_TYPE", "CLASSIFICATION_TYPE", "NORAD_CAT_ID", "ELEMENT_SET_NO",
            "REV_AT_EPOCH", "BSTAR", "MEAN_MOTION_DOT", "MEAN_MOTION_DDOT", "SEMIMAJOR_AXIS",
            "PERIOD", "APOAPSIS", "PERIAPSIS", "OBJECT_TYPE", "RCS_SIZE",
            "COUNTRY_CODE", "LAUNCH_DATE", "SITE", "DECAY_DATE", "FILE",
            "GP_ID", "TLE_LINE0", "TLE_LINE1", "TLE_LINE2"]


class GeneralPerturbations():
    def __init__(self, file_name=None, set_defaults=False):
        # Header
        # Relative metadata
        # Object
        #  Metadata, OD, State, Covariance
        # Comments are optional and not currently supported by this class

        self._keys_header = ['CCSDS_OMM_VERS', 'COMMENT', 'CREATION_DATE', 'ORIGINATOR']
        self._keys_relative_metadata = ["CENTER_NAME", "REF_FRAME", "TIME_SYSTEM", "MEAN_ELEMENT_THEORY"]
        self._keys_metadata = ["OBJECT_NAME", "OBJECT_ID", "EPOCH", "MEAN_MOTION", "ECCENTRICITY", "INCLINATION",
                               "RA_OF_ASC_NODE", "ARG_OF_PERICENTER", "MEAN_ANOMALY", "EPHEMERIS_TYPE",
                               "CLASSIFICATION_TYPE", "NORAD_CAT_ID", "ELEMENT_SET_NO", "REV_AT_EPOCH", "BSTAR",
                               "MEAN_MOTION_DOT", "MEAN_MOTION_DDOT", "SEMIMAJOR_AXIS", "PERIOD", "APOAPSIS",
                               "PERIAPSIS", "OBJECT_TYPE", "RCS_SIZE",
                               "GP_ID", "TLE_LINE0", "TLE_LINE1", "TLE_LINE2"]
        self._keys_data_state = ['X', 'Y', 'Z', 'X_DOT', 'Y_DOT', 'Z_DOT']
        self._keys_data_covariance = ['CR_R', 'CT_R', 'CT_T', 'CN_R', 'CN_T', 'CN_N', 'CRDOT_R', 'CRDOT_T', 'CRDOT_N',
                                      'CRDOT_RDOT', 'CTDOT_R', 'CTDOT_T', 'CTDOT_N', 'CTDOT_RDOT', 'CTDOT_TDOT',
                                      'CNDOT_R', 'CNDOT_T', 'CNDOT_N', 'CNDOT_RDOT', 'CNDOT_TDOT', 'CNDOT_NDOT',
                                      'CDRG_R', 'CDRG_T', 'CDRG_N', 'CDRG_RDOT', 'CDRG_TDOT', 'CDRG_NDOT', 'CDRG_DRG',
                                      'CSRP_R', 'CSRP_T', 'CSRP_N', 'CSRP_RDOT', 'CSRP_TDOT', 'CSRP_NDOT', 'CSRP_DRG',
                                      'CSRP_SRP', 'CTHR_R', 'CTHR_T', 'CTHR_N', 'CTHR_RDOT', 'CTHR_TDOT', 'CTHR_NDOT',
                                      'CTHR_DRG', 'CTHR_SRP', 'CTHR_THR']
        self._keys_extra = ["COUNTRY_CODE", "LAUNCH_DATE", "SITE", "DECAY_DATE", "FILE"]

        self._keys_header_obligatory = ['CCSDS_OMM_VERS', 'COMMENT', 'CREATION_DATE', 'ORIGINATOR']
        self._keys_relative_metadata_obligatory = ['TCA', 'MISS_DISTANCE']
        self._keys_metadata_obligatory = ['OBJECT', 'OBJECT_NAME', "GP_ID", "TLE_LINE0", "TLE_LINE1", "TLE_LINE2"]

        self._keys_data_state_obligatory = ['X', 'Y', 'Z', 'X_DOT', 'Y_DOT', 'Z_DOT']  # 位置和速度
        self._keys_data_covariance_obligatory = ['CR_R', 'CT_R', 'CT_T', 'CN_R', 'CN_T', 'CN_N', 'CRDOT_R', 'CRDOT_T',
                                                 'CRDOT_N', 'CRDOT_RDOT', 'CTDOT_R', 'CTDOT_T', 'CTDOT_N', 'CTDOT_RDOT',
                                                 'CTDOT_TDOT', 'CNDOT_R', 'CNDOT_T', 'CNDOT_N', 'CNDOT_RDOT',
                                                 'CNDOT_TDOT', 'CNDOT_NDOT']

        self._values_header = dict.fromkeys(self._keys_header)
        self._values_relative_metadata = dict.fromkeys(self._keys_relative_metadata)
        self._values_metadata = dict.fromkeys(self._keys_metadata)

        self._values_data_state = dict.fromkeys(self._keys_data_state)
        self._values_data_covariance = dict.fromkeys(self._keys_data_covariance)
        self._values_extra = dict.fromkeys(self._keys_extra)  # This holds extra key, value pairs associated with each CDM object, used internally by the kessler codebase and not a part of the CDM standard

        self._keys_with_dates = ['CREATION_DATE', 'EPOCH', "LAUNCH_DATE", 'DECAY_DATE']
        if set_defaults:
            self.set_header('CCSDS_OMM_VERS', '2.0')
            self.set_header('CREATION_DATE', datetime.datetime.utcnow().isoformat())

        if file_name:
            self.copy_from(GeneralPerturbations.load(file_name))

    def copy(self):
        ret = GeneralPerturbations()
        ret._values_header = copy.deepcopy(self._values_header)
        ret._values_relative_metadata = copy.deepcopy(self._values_relative_metadata)
        ret._values_metadata = copy.deepcopy(self._values_metadata)
        ret._values_data_state = copy.deepcopy(self._values_data_state)
        ret._values_data_covariance = copy.deepcopy(self._values_data_covariance)
        return ret

    def copy_from(self, other_gp):
        self._values_header = copy.deepcopy(other_gp._values_header)
        self._values_relative_metadata = copy.deepcopy(other_gp._values_relative_metadata)
        self._values_metadata = copy.deepcopy(other_gp._values_metadata)
        self._values_data_state = copy.deepcopy(other_gp._values_data_state)
        self._values_data_covariance = copy.deepcopy(other_gp._values_data_covariance)

    def to_dict(self):
        data = {}
        data_header = dict.fromkeys(self._keys_header)
        for key, value in self._values_header.items():
            data_header[key] = value
        data.update(data_header)

        data_relative_metadata = dict.fromkeys(self._keys_relative_metadata)
        for key, value in self._values_relative_metadata.items():
            data_relative_metadata[key] = value
        data.update(data_relative_metadata)

        data_metadata = dict.fromkeys(self._keys_metadata)
        for key, value in self._values_metadata.items():
            data_metadata[key] = value
        data.update(data_metadata)

        data_data_state = dict.fromkeys(self._keys_data_state)
        for key, value in self._values_data_state.items():
            data_data_state[key] = value
        data.update(data_data_state)

        data_data_covariance = dict.fromkeys(self._keys_data_covariance)
        for key, value in self._values_data_covariance.items():
            data_data_covariance[key] = value
        data.update(data_data_covariance)

        data_extra = dict.fromkeys(self._keys_extra)
        for key, value in self._values_extra.items():
            data_extra[key] = value
        data.update(data_extra)

        return data

    def kvn(self, show_all=False):
        pass
        return True

    def to_dataframe(self):
        data = self.to_dict()
        return pd.DataFrame(data, index=[0])

    def save(self, file_name):
        content = self.kvn()
        with open(file_name, 'w') as f:
            f.write(content)

    def __hash__(self):
        return hash(self.kvn(show_all=True))

    def __eq__(self, other):
        if isinstance(other, GeneralPerturbations):
            return hash(self) == hash(other)
        return False

    def set_header(self, key, value):
        if key in self._keys_header:
            if key in self._keys_with_dates:
                # We have a field with a date string as the value. Check if the string is in the format needed by the CCSDS 508.0-B-1 standard
                try:
                    if not value:  # value非空
                        _ = datetime.datetime.strptime(value, '%Y-%m-%dT%H:%M:%S.%f')
                    else:
                        _ = ''
                except Exception as e:
                    raise RuntimeError('{} ({}) is not in the expected format.\n{}'.format(key, value, str(e)))
            self._values_header[key] = value
        else:
            raise ValueError('Invalid key ({}) for header'.format(key))

    def set_relative_metadata(self, key, value):
        if key in self._keys_relative_metadata:
            self._values_relative_metadata[key] = value
        else:
            raise ValueError('Invalid key ({}) for relative metadata'.format(key))

    def set_metadata(self, key, value):
        if key in self._keys_metadata:
            self._values_metadata[key] = value
        elif key in self._keys_data_state:
            self._values_data_state[key] = value
        elif key in self._keys_data_covariance:
            self._values_data_covariance[key] = value
        else:
            raise ValueError('Invalid key ({}) for object data'.format(key))

    def set_extra(self, key, value):
        if key in self._keys_extra:
            self._values_extra[key] = value
        else:
            raise ValueError('Invalid key ({}) for relative metadata'.format(key))

    def get_object(self, key):
        if key in self._keys_metadata:
            return self._values_metadata[key]
        elif key in self._keys_data_state:
            return self._values_data_state[key]
        elif key in self._keys_data_covariance:
            return self._values_data_covariance[key]
        else:
            raise ValueError('Invalid key ({}) for object data'.format(key))

    def get_relative_metadata(self, key):
        if key in self._keys_relative_metadata:
            return self._values_relative_metadata[key]
        else:
            raise ValueError('Invalid key ({}) for relative metadata'.format(key))

    def __repr__(self):  # 实例化对象输出信息
        return self.kvn()

    def __getitem__(self, key):  # 建立类似字典访问结构
        return self.to_dict()[key]

    def __setitem__(self, key, value):
        if key in self._keys_header:
            self.set_header(key, value)
        elif key in self._keys_relative_metadata:
            self.set_relative_metadata(key, value)
        elif key in self._keys_metadata:
            self.set_metadata(key, value)
        elif key in self._keys_extra:
            self.set_extra(key, value)
        else:
            raise ValueError('Invalid key: {}'.format(key))


GP = GeneralPerturbations










