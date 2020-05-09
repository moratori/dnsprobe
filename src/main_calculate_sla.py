#!/usr/bin/env python3

"""
docstring is here
"""

import datetime
import traceback
import sys

import common.common.framework as framework
import common.data.dao as dao
import common.data.types as types


class SLACalculator(framework.SetupwithInfluxdb):

    def __init__(self):
        super().__init__(__name__, __file__)

    def calculate_DNS_name_server_availability(self):

        calc_range = self.cnfs.constants.calculation_range_in_minutes
        end_time = self.criteria.isoformat() + "Z"
        start_time = (self.criteria - datetime.timedelta(
            minutes=calc_range)).isoformat() + "Z"

        self.logger.info("calculation range: %s - %s" % (
            start_time, end_time))

        calculation_target = self.dao.get_af_dst_name_combination()
        self.logger.info("calculation_target: %s" % str(calculation_target))

        result = []

        for (dst_name, afs) in calculation_target.items():
            for af in afs:

                self.logger.info("calculation start for %s %s" % (
                    dst_name, af))

                total_measurements = self.dao.count_total_measurements(
                    dst_name, af, start_time, end_time)

                failed_measurements = self.dao.count_failed_measurements(
                    dst_name, af, start_time, end_time)

                self.logger.info("failed / total =  %d / %d" % (
                    failed_measurements, total_measurements))

                sla_value = 100
                if total_measurements != 0:
                    successful = \
                        float(total_measurements - failed_measurements)
                    sla_value = (successful / total_measurements) * 100
                else:
                    self.logger.warning("number of total measurement is zero!")

                self.logger.info("calculated sla = %f" % sla_value)

                result.append(types.DNS_name_server_availability(end_time,
                                                                 start_time,
                                                                 dst_name,
                                                                 af,
                                                                 sla_value))

        self.dao_nameserver_availability.write_measurement_data(result)

    def setup_application(self):
        self.dao = dao.Mes_cq_nameserver_availability(self)
        self.dao_nameserver_availability = \
            dao.Mes_nameserver_availability(self)
        self.criteria = datetime.datetime.utcnow()

    def run_application(self):
        self.calculate_DNS_name_server_availability()


def main():
    try:
        calc = SLACalculator()
    except Exception:
        # LOGGERのセットアップ自体にも失敗している可能性ありの為
        # 標準出力にログ出力
        print(traceback.format_exc())
        sys.exit(1)

    calc.start()


if __name__ == "__main__":
    main()
