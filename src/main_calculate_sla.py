#!/usr/bin/env python3

"""
docstring is here
"""

import datetime
import traceback
import sys

import common.common.framework as framework
import common.data.dao as dao


class SLACalculator(framework.SetupwithInfluxdb):

    def __init__(self):
        super().__init__(__name__, __file__)

    def calculate_DNS_name_server_availability(self):

        current_time = self.criteria
        starting_time = current_time - datetime.timedelta(
            minutes=self.cnfs.constants.calculation_range_in_minutes)

        self.logger.info("calculation range: %s - %s" % (
            starting_time, current_time))

        calculation_target = self.dao.get_af_dst_name_combination()
        self.logger.info("calculation_target: %s" % str(calculation_target))

        for (dst_name, afs) in calculation_target.items():
            for af in afs:

                self.logger.info("calculation start for %s %s" % (
                    dst_name, af))

                total_measurements = self.dao.count_total_measurements(
                    dst_name, af, starting_time, current_time)

                self.logger.info("total %d for %s %s while %s - %s" % (
                    total_measurements,
                    dst_name,
                    af,
                    str(starting_time),
                    str(current_time)))

                failed_measurements = self.dao.count_failed_measurements(
                    dst_name, af, starting_time, current_time)

                self.logger.info("failed %d for %s %s while %s - %s" % (
                    failed_measurements,
                    dst_name,
                    af,
                    str(starting_time),
                    str(current_time)))

                sla = 100
                if total_measurements != 0:
                    successful = \
                        float(total_measurements - failed_measurements)
                    sla = (successful / total_measurements) * 100
                else:
                    self.logger.warning("number of total measurement is zero!")

                self.logger.info("calculated sla = %f" % sla)

    def setup_application(self):
        self.dao = dao.MES_CQ_Nameserver_Availability(self)
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
