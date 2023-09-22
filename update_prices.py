from apscheduler.schedulers.background import BackgroundScheduler
from utils import update_inventory_prices


if __name__ == '__main__':
    scheduler = BackgroundScheduler()
    scheduler.add_job(update_inventory_prices, 'interval',
                      hours=2)
    scheduler.start()

    try:
        while True:
            pass
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        