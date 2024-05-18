from logger import log
from fsm_stenographer_service import fsm_stenographer_service


RESTARTN = 10


def main():

    log.info("fsm-stenographer server is starting...")

    reset = RESTARTN
    while True:
        if reset == 0:
            log.warning(
                f"fsm-stenographer server is out of restart trials"
            )
            break
        try:
            fsm_stenographer_service.read_and_process_event()
        except Exception as ex:
            log.warning(
                f"fsm-stenographer server is stopped because of exception: {ex}"
            )
            reset -= 1


if __name__ == "__main__":
    main()
