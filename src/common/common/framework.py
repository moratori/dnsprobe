#!/usr/bin/env python

import common.common.logger as logger
import common.common.config as config

import re
import os
import configparser
import namedtupled
import sys
import traceback
import json

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
        self.load_config()
        self.validate_config()
        self.setup_logger()
        self.load_tmpdata()

    def load_tmpdata(self):

        tmpfilename = os.path.join(config.TMP_DIR, self.script_name)

        if not (os.path.isdir(config.TMP_DIR) and os.path.isfile(tmpfilename)):
            self.logger.info("tmpdata file(%s) not found. loading skipped" %
                             (tmpfilename))
            self.tmp_data = {}
            return

        try:
            with open(tmpfilename, "r", encoding="utf8") as handle:
                    self.tmp_data = json.load(handle)
            self.logger.info("reading finished in properly")
        except Exception as ex:
            self.logger.warning("unable to load tmpdata from %s: %s" %
                                (tmpfilename, str(ex)))
            self.tmp_data = {}

        self.logger.debug("tmp data loaded: %s" % (self.tmp_data))

    def write_tmpdata(self):

        # 排他制御はないので、バッチの起動制御で対応する

        tmpfilename = os.path.join(config.TMP_DIR, self.script_name)

        if not os.path.isdir(config.TMP_DIR):
            try:
                os.mkdir(config.TMP_DIR)
            except FileExistsError as ex:
                self.logger.warning("fileexists error while making dir: %s" %
                                    (str(ex)))
            except Exception as ex:
                self.logger.warning("error occurred while making dir: %s" %
                                    (str(ex)))
                self.logger.error("unable to make directory")
                return
        try:
            with open(tmpfilename, "w", encoding="utf8") as handle:
                json.dump(self.tmp_data, handle)
            self.logger.info("writing finished in properly")
        except Exception as ex:
            self.logger.warning("unable to write tmp data to %s: %s" %
                                (tmpfilename, str(ex)))

    def convert_config_type(self, config):
        if isinstance(config, str):
            string_type = re.compile("^(\".*\"|'.*')$")
            integer_type = re.compile("^[0-9]+$")
            float_type = re.compile("^[0-9]+\.[0-9]+$")
            boolean_type = re.compile("^(true|false)$")
            if string_type.findall(config):
                return config.strip("\"'")
            elif integer_type.findall(config):
                return int(config)
            elif float_type.findall(config):
                return float(config)
            elif boolean_type.findall(config.lower()):
                return "true" in config.lower()
            else:
                return config
        elif isinstance(config, dict):
            result = dict()
            for (key, value) in config.items():
                result[key] = self.convert_config_type(value)
            return result
        else:
            pass  # sould occurr an error

    def load_config(self):
        specific_config_basename = os.path.basename(
            self.script_name).replace(BaseSetup.SCRIPT_EXT, BaseSetup.CONF_EXT)

        general_conf = configparser.ConfigParser()
        specific_conf = configparser.ConfigParser()

        general_conf.read(os.path.join(config.CONFIG_DIR,
                                       BaseSetup.GENERAL_CONF_NAME))
        specific_conf.read(os.path.join(config.CONFIG_DIR,
                                        specific_config_basename))

        self.cnfg = namedtupled.map(self.convert_config_type(
            general_conf._sections))
        self.cnfs = namedtupled.map(self.convert_config_type(
            specific_conf._sections))

        self.validate_config()

    def validate_config(self):
        pass

    def setup_logger(self):
        self.logger = logger.setup_logger(self.module_name,
                                          self.script_name,
                                          self.cnfg.logging.loglevel,
                                          self.cnfg.logging.rotation_timing,
                                          self.cnfg.logging.backupcount)

    def setup_application(self):
        pass

    def run(self, **args):
        pass

    def teardown_resource(self):
        pass

    def start(self, **args):
        retcode = 0
        try:
            self.logger.info("application started")
            self.logger.info("application setup started")
            self.setup_application()
            self.logger.info("application setup ended")
            self.logger.info("main routine started")
            result = self.run(**args)
            self.logger.info("main routine ended")
            self.logger.info("application ended without unexpected error")
            if (type(result) is int):
                retcode = result
        except KeyboardInterrupt:
            self.logger.warn("keyboard interrupted")
            retcode = 1
        except Exception as ex:
            self.logger.error("unexpected exception <%s> occurred" % (str(ex)))
            self.logger.error(traceback.format_exc())
            retcode = 2
        finally:
            self.teardown_resource()

        sys.exit(retcode)


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

    def teardown_resource(self):
        try:
            self.session.close()
        except Exception:
            pass


class SetupwithInfluxdb(BaseSetup):

    def __init__(self, module_name, script_name):
        super().__init__(module_name, script_name)
        self.setup_session()

    def setup_session(self):
        host = self.cnfg.data_store.host
        port = self.cnfg.data_store.port
        ssl = self.cnfg.data_store.ssl
        user = self.cnfg.data_store.user
        passwd = self.cnfg.data_store.passwd
        database = self.cnfg.data_store.database
        self.session = InfluxDBClient(host,
                                      port,
                                      user,
                                      passwd,
                                      database,
                                      verify_ssl=ssl,
                                      ssl=ssl)

    def teardown_resource(self):
        try:
            self.session.close()
        except Exception:
            pass
