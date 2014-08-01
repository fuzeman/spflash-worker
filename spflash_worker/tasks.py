from celery import Celery
from pyvirtualdisplay import Display
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import logging
import os
import time

display = Display()
display.start()

log = logging.getLogger(__name__)

cel = Celery()
cel.conf.update(
    BROKER_URL=os.environ.get('CELERY_BROKER', 'redis://localhost:6379'),
    CELERY_RESULT_BACKEND=os.environ.get('CELERY_BACKEND', 'redis://localhost:6379'),
)

hostname = os.environ.get('HOSTNAME', 'localhost:5455')
drivers = {}


@cel.task(name='spflash.get')
def get(version, ping):
    driver = get_driver(version)
    log.debug("Using driver: %s", driver)

    result = sp_run(driver, ping)
    log.debug("Result: %s", repr(result))

    return result


def sp_run(driver, ping, retry=3):
    for x in xrange(retry):
        try:
            return driver.execute_script("return document.getElementById('SPFBIn_2072_player').sp_run(arguments[0])", ping)
        except WebDriverException, ex:
            log.warn(ex)
            time.sleep(1)

    return None


def get_driver(version):
    if version not in drivers:
        log.debug("Constructing driver...")
        drivers[version] = webdriver.PhantomJS()

        log.debug("Loading host page...")
        drivers[version].get("http://%s/%s/host" % (hostname, version))

        log.debug("Waiting for page to finish loading...")
        WebDriverWait(drivers[version], 10).until(EC.presence_of_element_located((By.ID, "SPFBIn_2072_player")))

    return drivers[version]
