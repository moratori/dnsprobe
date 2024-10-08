#!/usr/bin/env python

import re
import os
import configparser
import sys
import traceback
import json
import threading

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from influxdb import InfluxDBClient

import common.common.logger as logger
import common.common.config as config
import common.common.util as util


class BaseSetup(object):

    SCRIPT_EXT = ".py"
    CONF_EXT = ".ini"
    GENERAL_CONF_NAME = "general" + CONF_EXT

    RET_NORMAL_END = 0
    RET_KEY_INTERRUPTED_END = 1
    RET_ABNORMAL_END = 100

    def __init__(self, module_name, script_name):
        self.module_name = module_name
        self.script_name = script_name
        self.tmp_data = {}
        self.load_config()
        self.validate_config()
        self.prepare_logger()
        self.tmp_data_mutex = threading.BoundedSemaphore(value=1)

    def load_tmpdata(self):

        specific_config_basename = os.path.basename(self.script_name)

        tmpfilename = os.path.join(config.TMP_DIR,
                                   specific_config_basename)

        if not (os.path.isdir(config.TMP_DIR) and os.path.isfile(tmpfilename)):
            self.logger.info("tmpdata file(%s) not found. loading skipped" %
                             (tmpfilename))
            self.tmp_data = {}
            return

        try:
            with self.tmp_data_mutex,\
                    open(tmpfilename, "r", encoding="utf8") as handle:
                self.tmp_data = json.load(handle)
            self.logger.info("loading finished in properly")
        except Exception as ex:
            self.logger.warning("unable to load tmpdata from %s: %s" %
                                (tmpfilename, str(ex)))
            self.tmp_data = {}

        self.logger.debug("tmp data loaded: %s" % (self.tmp_data))

    def write_tmpdata(self):

        specific_config_basename = os.path.basename(self.script_name)

        tmpfilename = os.path.join(config.TMP_DIR,
                                   specific_config_basename)

        with self.tmp_data_mutex:
            try:
                if not os.path.isdir(config.TMP_DIR):
                    try:
                        os.mkdir(config.TMP_DIR)
                    except FileExistsError as ex:
                        self.logger.warning(
                            "fileexists error while making dir: %s"
                            % (str(ex)))
                    except Exception as ex:
                        self.logger.warning(
                            "error occurred while making dir: %s"
                            % (str(ex)))
                        self.logger.error("unable to make directory")
                        return
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
            float_type = re.compile(r"^[0-9]+\.[0-9]+$")
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

        self.cnfg = util.recursive_namedtuple(self.convert_config_type(
            general_conf._sections))
        self.cnfs = util.recursive_namedtuple(self.convert_config_type(
            specific_conf._sections))

        self.validate_config()

    def validate_config(self):
        pass

    def prepare_logger(self):
        self.logger = logger.setup_logger(self.module_name,
                                          self.script_name,
                                          self.cnfg.logging.loglevel,
                                          self.cnfg.logging.rotation_timing,
                                          self.cnfg.logging.backupcount)

    def setup_resource(self):
        pass

    def setup_application(self):
        pass

    def run_application(self, **args):
        pass

    def teardown_application(self):
        pass

    def teardown_resource(self):
        pass

    def start(self, **args):
        retcode = BaseSetup.RET_NORMAL_END
        try:
            self.logger.info("start as application")

            self.logger.info("start setup resource")
            self.setup_resource()
            self.logger.info("end setup resource")

            self.logger.info("start application setup")
            self.setup_application()
            self.logger.info("end application setup")

            self.logger.info("start main routine")
            result = self.run_application(**args)
            self.logger.info("end main routine")

            self.logger.info("end application without unexpected error")
            if (type(result) is int):
                retcode = result
        except KeyboardInterrupt:
            self.logger.warn("keyboard interrupted")
            retcode = BaseSetup.RET_KEY_INTERRUPTED_END
        except Exception as ex:
            self.logger.error("unexpected exception <%s> occurred" % (str(ex)))
            self.logger.error(traceback.format_exc())
            retcode = BaseSetup.RET_ABNORMAL_END
        finally:
            self.logger.info("start cleanup")
            try:
                self.logger.info("start teardown application")
                self.teardown_application()
                self.logger.info("end teardown application")
            except Exception as ex:
                self.logger.warning("unexpected exception <%s> occurred" %
                                    str(ex))
            try:
                self.logger.info("start teardown resource")
                self.teardown_resource()
                self.logger.info("end teardown resource")
            except Exception as ex:
                self.logger.warning("unexpected exception <%s> occurred" %
                                    str(ex))
            self.logger.info("end cleanup")

        sys.exit(retcode)


class SetupwithMySQLdb(BaseSetup):

    def __init__(self, module_name, script_name):
        super().__init__(module_name, script_name)

    def setup_resource(self):
        database_specifier = 'mysql://%s:%s@%s/%s?charset=utf8' % (
            self.cnfg.database.user,
            self.cnfg.database.passwd,
            self.cnfg.database.host,
            self.cnfg.database.dbname
        )
        self.dbengine = create_engine(database_specifier,
                                      echo=False)

        session = scoped_session(sessionmaker(autocommit=False,
                                              autoflush=False,
                                              bind=self.dbengine))
        self.session = session

    def teardown_resource(self):
        self.session.close()


class SetupwithInfluxdb(BaseSetup):

    def __init__(self, module_name, script_name):
        super().__init__(module_name, script_name)

    def setup_resource(self):
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
        self.session.close()
