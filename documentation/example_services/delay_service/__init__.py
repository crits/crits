import logging
import time

from crits.services.core import Service, ServiceConfigOption

logger = logging.getLogger(__name__)


class DelayService(Service):
    name = "delay"
    version = '1.0.0'
    type_ = Service.TYPE_CUSTOM
    default_config = [
        ServiceConfigOption('sleep_time',
                            ServiceConfigOption.INT,
                            description="Number of seconds to"
                                        " sleep between notifications.",
                            default=5),
    ]

    @staticmethod
    def valid_for(obj):
        return

    def run(self, obj, config):
        for i in xrange(5):
            self._info(i)
            logger.info(i)
            self._info("sleeping")
            logger.info("sleeping")
            self._notify()
            time.sleep(self.config['sleep_time'])

