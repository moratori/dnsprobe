#!/usr/bin/env python

import common.common.logger as logger
import common.common.config as config

import os
import argparse
import configparser
import namedtupled
import sys
import traceback

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from influxdb import InfluxDBClient


class BaseSetup(object):

    SCRIPT_EXT = ".py"
    CONF_EXT = ".ini"
    GENERAL_CONF_NAME = "general" + CONF_EXT

    def __init__(self, module_name, script_name):
        self.module_name = module_name
        self.script_name = script_name
        self.setup_commandline_argument()
        self.validate_commandline_argument()
        self.load_config()
        self.validate_config()
        self.setup_logger()

    def setup_commandline_argument(self):
        argparser = argparse.ArgumentParser()
        self.args = argparser.parse_args()

        self.validate_commandline_argument()

    def validate_commandline_argument(self):
        pass

    def load_config(self):
        specific_config_basename = os.path.basename(
            self.script_name).replace(BaseSetup.SCRIPT_EXT, BaseSetup.CONF_EXT)

        general_conf = configparser.ConfigParser()
        specific_conf = configparser.ConfigParser()

        general_conf.read(os.path.join(config.CONFIG_DIR,
                                       BaseSetup.GENERAL_CONF_NAME))
        specific_conf.read(os.path.join(config.CONFIG_DIR,
                                        specific_config_basename))

        self.cnfg = namedtupled.map(general_conf._sections)
        self.cnfs = namedtupled.map(specific_conf._sections)

        self.validate_config()

    def validate_config(self):
        pass

    def setup_logger(self):
        self.logger = logger.setup_logger(self.module_name,
                                          self.script_name,
                                          self.cnfg.logging.loglevel,
                                          self.cnfg.logging.rotation_timing,
                                          self.cnfg.logging.backupcount)

    def run(self, **args):
        pass

    def start(self, **args):
        try:
            self.logger.info("starting main routine")
            self.run(**args)
            self.logger.info("main routine completed in successfully")
        except Exception as ex:
            self.logger.error("unexpected exception <%s> occurred" % (str(ex)))
            self.logger.error(traceback.format_exc())
            sys.exit(1)
        sys.exit(0)


class SetupwithMySQLdb(BaseSetup):

    def __init__(self, module_name, script_name):
        super().__init__(module_name, script_name)
        self.setup_engine()
        self.setup_session()

    def setup_engine(self):
        database_specifier = 'mysql://%s:%s@%s/%s?charset=utf8' % (
            self.cnfg.database.user,
            self.cnfg.database.passwd,
            self.cnfg.database.host,
            self.cnfg.database.dbname
        )
        self.dbengine = create_engine(database_specifier,
                                      encoding="utf-8",
                                      echo=False)

    def setup_session(self):
        session = scoped_session(sessionmaker(autocommit=False,
                                              autoflush=False,
                                              bind=self.dbengine))
        self.session = session

    def start(self, **args):
        try:
            self.logger.info("starting main routine")
            self.run(**args)
            self.logger.info("main routine completed in successfully")
        except Exception as ex:
            self.logger.error("unexpected exception <%s> occurred" % (str(ex)))
            self.logger.error(traceback.format_exc())
            sys.exit(1)
        finally:
            self.session.close()
        sys.exit(0)


class SetupwithInfluxdb(BaseSetup):

    def __init__(self, module_name, script_name):
        super().__init__(module_name, script_name)
        self.setup()

    def setup(self):
        host = self.cnfg.data_store.host
        port = self.cnfg.data_store.port
        user = self.cnfg.data_store.user
        passwd = self.cnfg.data_store.passwd
        database = self.cnfg.data_store.database
        self.session = InfluxDBClient(host, int(port), user, passwd, database)

    def start(self, **args):
        try:
            self.logger.info("starting main routine")
            self.run(**args)
            self.logger.info("main routine completed in successfully")
        except Exception as ex:
            self.logger.error("unexpected exception <%s> occurred" % (str(ex)))
            self.logger.error(traceback.format_exc())
            sys.exit(1)
        finally:
            self.session.close()
        sys.exit(0)