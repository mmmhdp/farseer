from logger import log
from time import sleep
from outbox_service import outbox_service


RESTARTN = 50
TIME_DELAY_BETWEEN_UPDATES = 2
RESTART_DELAY = 2


def main():

    log.info("outbox server is starting...")

    reset = RESTARTN
    while True:
        if reset == 0:
            log.warning(
                f"outbox server is out of restart trials"
            )
            break
        try:
            sleep(TIME_DELAY_BETWEEN_UPDATES)
            outbox_service.update_state_with_preds()
        except Exception as ex:
            log.warning(
                f"outbox server is stopped because of exception: {ex}"
            )
            reset -= 1
            sleep(RESTART_DELAY)


if __name__ == "__main__":
    main()
