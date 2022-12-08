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

from setuptools import find_packages, setup

# install_requires = [
#     'pyspark===3.1.1',
#     # 'fastparquet===0.5.0',  # not using it. sticking to pyspark with spark cluster according to Nga
#     'findspark===1.4.2',
#     'flask===1.1.2', 'flask_restful===0.3.8', 'flask-restx===0.3.0',  # to create Flask server
#     'gevent===1.4.0', 'greenlet===0.4.16',  # to run flask server
#     'werkzeug===0.16.1',
#     'jsonschema',  # to verify json objects
#     'fastjsonschema===2.15.1',
#     'boto3', 'botocore',
# ]

install_requires = [
    'pyspark===3.1.2',
    # 'fastparquet===0.5.0',  # not using it. sticking to pyspark with spark cluster according to Nga
    'findspark===1.4.2',
    'flask===2.0.1', 'flask_restful===0.3.9', 'flask-restx===0.5.0',  # to create Flask server
    'gevent===21.8.0', 'greenlet===1.1.1',  # to run flask server
    'werkzeug===2.0.1',
    'jsonschema',  # to verify json objects
    'fastjsonschema===2.15.1',
    'requests===2.26.0',
    'boto3', 'botocore',
]

setup(
    name="parquet_ingestion_search",
    version="0.0.1",
    packages=find_packages(),
    install_requires=install_requires,
    author="Apache SDAP",
    author_email="dev@sdap.apache.org",
    python_requires="==3.7",
    license='NONE',
    include_package_data=True,
)
