from logger import log
from fsm_stenographer import fsm_stenographer_service


def main():

    log.info("fsm-stenographer server is starting...")
    while True:
        try:
            fsm_stenographer_service.read_and_process_event()
        except Exception as ex:
            log.warning(
                f"fsm-stenographer server is stopped because of exception: {ex}"
            )


if __name__ == "__main__":
    main()
