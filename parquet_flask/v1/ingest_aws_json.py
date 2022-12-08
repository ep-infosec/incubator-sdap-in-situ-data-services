# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging
import os
import uuid
from multiprocessing.context import Process

from parquet_flask.aws.aws_s3 import AwsS3
from parquet_flask.io_logic.cdms_constants import CDMSConstants
from parquet_flask.io_logic.ingest_new_file import IngestNewJsonFile
from parquet_flask.io_logic.metadata_tbl_io import MetadataTblIO
from parquet_flask.utils.file_utils import FileUtils
from parquet_flask.utils.time_utils import TimeUtils

LOGGER = logging.getLogger(__name__)


class IngestAwsJsonProps:
    def __init__(self):
        self.__s3_url = None
        self.__s3_sha_url = None
        self.__uuid = str(uuid.uuid4())
        self.__working_dir = f'/tmp/{str(uuid.uuid4())}'
        self.__is_replacing = False
        self.__is_sanitizing = True
        self.__wait_till_complete = True

    @property
    def wait_till_complete(self):
        return self.__wait_till_complete

    @wait_till_complete.setter
    def wait_till_complete(self, val):
        """
        :param val:
        :return: None
        """
        self.__wait_till_complete = val
        return

    @property
    def is_sanitizing(self):
        return self.__is_sanitizing

    @is_sanitizing.setter
    def is_sanitizing(self, val):
        """
        :param val:
        :return: None
        """
        self.__is_sanitizing = val
        return

    @property
    def s3_sha_url(self):
        return self.__s3_sha_url

    @s3_sha_url.setter
    def s3_sha_url(self, val):
        """
        :param val:
        :return: None
        """
        self.__s3_sha_url = val
        return

    @property
    def is_replacing(self):
        return self.__is_replacing

    @is_replacing.setter
    def is_replacing(self, val):
        """
        :param val:
        :return: None
        """
        self.__is_replacing = val
        return

    @property
    def working_dir(self):
        return self.__working_dir

    @working_dir.setter
    def working_dir(self, val):
        """
        :param val:
        :return: None
        """
        self.__working_dir = val
        return

    @property
    def s3_url(self):
        return self.__s3_url

    @s3_url.setter
    def s3_url(self, val):
        """
        :param val:
        :return: None
        """
        self.__s3_url = val
        return

    @property
    def uuid(self):
        return self.__uuid

    @uuid.setter
    def uuid(self, val):
        """
        :param val:
        :return: None
        """
        self.__uuid = val
        return


class IngestAwsJson:
    def __init__(self, props=IngestAwsJsonProps()):
        self.__props = props
        self.__saved_file_name = None
        self.__ingested_date = TimeUtils.get_current_time_unix()
        self.__file_sha512 = None
        self.__sha512_result = None
        self.__sha512_cause = None
        self.__db_io = MetadataTblIO()

    def __get_s3_sha512(self):
        """
        sha512 file is in this format
        <sha-512><space or tab><s3 json filename>
        :return:
        """
        if self.__props.s3_sha_url is None:
            LOGGER.warning(f's3_sha_url is None. using s3_url to generate one')
            self.__props.s3_sha_url = f'{self.__props.s3_url}.sha512'
        s3 = AwsS3().set_s3_url(self.__props.s3_sha_url)
        try:
            s3.get_s3_obj_size()
            sha512_content = s3.read_small_txt_file()
            return sha512_content.replace(os.path.basename(self.__props.s3_url), '').strip()
        except:
            LOGGER.exception(f'cannot find s3_sha_url')
            return None

    def __compare_sha512(self, s3_sha512):
        if s3_sha512 is None:
            self.__sha512_result = False
            self.__sha512_cause = 'missing S3 sha512'
            return
        if s3_sha512 == self.__file_sha512:
            self.__sha512_result = True
            self.__sha512_cause = ''
            return
        self.__sha512_result = False
        self.__sha512_cause = f'mismatched sha512: {s3_sha512} vs {self.__file_sha512}'
        return

    def __execute_ingest_data(self):
        try:
            LOGGER.debug(f'ingesting file: {self.__saved_file_name}')
            start_time = TimeUtils.get_current_time_unix()
            ingest_new_file = IngestNewJsonFile(self.__props.is_replacing)
            ingest_new_file.sanitize_record = self.__props.is_sanitizing
            num_records = ingest_new_file.ingest(self.__saved_file_name, self.__props.uuid)
            end_time = TimeUtils.get_current_time_unix()
            LOGGER.debug(f'uploading to metadata table')
            new_record = {
                CDMSConstants.s3_url_key: self.__props.s3_url,
                CDMSConstants.uuid_key: self.__props.uuid,
                CDMSConstants.ingested_date_key: self.__ingested_date,
                CDMSConstants.file_size_key: FileUtils.get_size(self.__saved_file_name),
                CDMSConstants.checksum_key: self.__file_sha512,
                CDMSConstants.checksum_validation: self.__sha512_result,
                CDMSConstants.checksum_cause: self.__sha512_cause,
                CDMSConstants.job_start_key: start_time,
                CDMSConstants.job_end_key: end_time,
                CDMSConstants.records_count_key: num_records,
            }
            if self.__props.is_replacing:
                self.__db_io.replace_record(new_record)
            else:
                self.__db_io.insert_record(new_record)
            LOGGER.debug(f'deleting used file')
            FileUtils.del_file(self.__saved_file_name)
            # TODO make it background process?
            LOGGER.warning('Disabled tagging S3 due to IAM issues')
            # LOGGER.debug(f'tagging s3')
            # s3.add_tags_to_obj({
            #     'parquet_ingested': TimeUtils.get_time_str(self.__ingested_date),
            #     'job_id': self.__props.uuid,
            # })
        except Exception as e:
            LOGGER.debug(f'deleting error file')
            FileUtils.del_file(self.__saved_file_name)
            return {'message': 'failed to ingest to parquet', 'details': str(e)}, 500
        if self.__sha512_result is True:
            return {'message': 'ingested', 'job_id': self.__props.uuid}, 201
        return {'message': 'ingested, different sha512', 'cause': self.__sha512_cause,
                'job_id': self.__props.uuid}, 203

    def ingest(self):
        """
        - download s3 file
        - unzip if needed
        - ingest to parquet
        - update to metadata tbl
        - delete local file
        - tag s3 object

        :return: tuple - (json object, return code)
        """
        try:
            LOGGER.debug(f'starting to ingest: {self.__props.s3_url}')
            existing_record = self.__db_io.get_by_s3_url(self.__props.s3_url)
            if existing_record is None and self.__props.is_replacing is True:
                LOGGER.error(f'unable to replace file as it is new. {self.__props.s3_url}')
                return {'message': 'unable to replace file as it is new'}, 500

            if existing_record is not None and self.__props.is_replacing is False:
                LOGGER.error(f'unable to ingest file as it is already ingested. {self.__props.s3_url}. ingested record: {existing_record}')
                return {'message': 'unable to ingest file as it is already ingested'}, 500

            s3 = AwsS3().set_s3_url(self.__props.s3_url)
            LOGGER.debug(f'downloading s3 file: {self.__props.uuid}')
            FileUtils.mk_dir_p(self.__props.working_dir)
            self.__saved_file_name = s3.download(self.__props.working_dir)
            self.__file_sha512 = FileUtils.get_checksum(self.__saved_file_name)
            if self.__saved_file_name.lower().endswith('.gz'):
                LOGGER.debug(f's3 file is in gzipped form. unzipping. {self.__saved_file_name}')
                self.__saved_file_name = FileUtils.gunzip_file_os(self.__saved_file_name)
            self.__compare_sha512(self.__get_s3_sha512())
            if self.__props.wait_till_complete is True:
                return self.__execute_ingest_data()
            else:
                bg_process = Process(target=self.__execute_ingest_data, args=())
                bg_process.daemon = True
                bg_process.start()
                return {'message': 'ingesting. Not waiting.', 'job_id': self.__props.uuid}, 204
        except Exception as e:
            LOGGER.debug(f'deleting error file')
            FileUtils.del_file(self.__saved_file_name)
            return {'message': 'failed to ingest to parquet', 'details': str(e)}, 500
