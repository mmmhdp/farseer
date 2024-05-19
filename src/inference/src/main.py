from logger import log
from runner_service import runner_service


RESTARTN = 10


def main():

    log.info("runner server is starting...")

    reset = RESTARTN
    while True:
        if reset == 0:
            log.warning(
                f"runner server is out of restart trials"
            )
            break
        # try:
        runner_service.read_and_process_event()
        # except Exception as ex:
        #    log.warning(
        #        f"runner server is stopped because of exception: {ex}"
        #    )
        #    reset -= 1


if __name__ == "__main__":
    main()
