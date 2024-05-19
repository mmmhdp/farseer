from logger import log
from inference_service import inference_service


RESTARTN = 10


def main():

    log.info("inference server is starting...")

    reset = RESTARTN
    while True:
        if reset == 0:
            log.warning(
                f"inference server is out of restart trials"
            )
            break
        try:
            inference_service.read_and_process_event()
        except Exception as ex:
            log.warning(
                f"inference server is stopped because of exception: {ex}"
            )
            reset -= 1


if __name__ == "__main__":
    main()
