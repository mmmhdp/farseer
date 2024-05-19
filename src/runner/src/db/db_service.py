import os
import uuid
import pathlib
import urllib3
from io import BytesIO

import numpy as np
import numpy.typing as npt
from dotenv import load_dotenv, find_dotenv
import redis
from minio import Minio
from minio.error import S3Error

from runner_models import Event
from logger import log

_env_file = find_dotenv(f'./.{os.getenv("ENV", "dev")}.env')
load_dotenv(_env_file)


class ProcessCacheDatabase():
    def __init__(self):
        self.host = self._get_host()
        self.port = self._get_port()
        self.__password = self._get_db_password()
        self.database = self._get_db()
        self.conn = redis.Redis(
            host=self.host,
            port=self.port,
            password=self.__password,
            db=self.database,
        )

    def __del__(self):
        self.conn.close()

    def _get_host(self):
        host = os.environ['REDIS_DB_HOST']
        return host

    def _get_port(self):
        port = os.environ['REDIS_DB_PORT']
        return port

    def _get_db_password(self):
        password = os.environ['REDIS_HOST_PASSWORD']
        return password

    def _get_db(self):
        db_partition = 0
        return db_partition

    def save_pid(self, pid: int, event: Event):
        self.conn.set(event.request_uuid, pid)

    def is_exists(self, event: Event):
        return self.conn.keys(event.request_uuid)

    def find_all_possible_pids_for_event(self, event) -> list[int]:
        cursor = '0'
        prefix = event.request_uuid
        ns_keys = prefix + '*'

        pids = []
        while cursor != 0:
            cursor, keys = self.conn.scan(
                cursor=cursor, match=ns_keys, count=10_000)
            if keys:
                for key in keys:
                    pid = self.conn.get(key.decode())
                    pid = int(pid.decode())
                    pids.append(pid)

        return pids

    def clear_after_event(self, event: Event):
        cursor = '0'
        ns_keys = event.request_uuid + '*'
        while cursor != 0:
            cursor, keys = self.conn.scan(
                cursor=cursor, match=ns_keys, count=10_000)
            if keys:
                self.conn.delete(*keys)


IMAGE_BUCKET_NAME = "image_bucket"


class ImgS3Database():
    def __init__(self):
        self.host = self._get_host()
        self.port = self._get_port()
        self.__access_key = self._get_db_user()
        self.__secret_key = self._get_db_password()
        self.endpoint = self._get_endpoint()
        self.client = Minio(
            endpoint=self.endpoint,
            access_key=self.__access_key,
            secret_key=self.__secret_key,
            secure=False
        )
        self.IMAGE_BUCKET_path = pathlib.Path(IMAGE_BUCKET_NAME)

    def __init_bucket(self):
        try:
            is_exists = self.client.bucket_exists(IMAGE_BUCKET_NAME)
            if not is_exists:
                self.client.make_bucket(IMAGE_BUCKET_NAME)
        except (S3Error, ValueError) as er:
            log.exception(f"tries to init bucket, but get ex: {er})")

    def _get_endpoint(self):
        url = f"{self.host}:{self.port}/"
        return url

    def _get_host(self):
        host = os.environ['MINIO_HOST']
        return host

    def _get_port(self):
        port = os.environ['MINIO_PORT']
        return port

    def _get_db_user(self):
        user = os.environ['MINIO_ROOT_USER']
        return user

    def _get_db_password(self):
        password = os.environ['MINIO_ROOT_PASSWORD']
        return password

    def save_frame(self, frame: npt.ArrayLike, event: Event) -> str:
        b_frame = frame.tobytes()
        frm_buff = BytesIO(b_frame)
        bucket_name = IMAGE_BUCKET_NAME
        content_type = "image/png"
        frm_obj_name = str(
            self.IMAGE_BUCKET_path / event.request_uuid / str(uuid.uuid4()))

        result = self.client.put_object(
            bucket_name=bucket_name,
            object_name=frm_obj_name,
            data=frm_buff,
            content_type=content_type)

        if result:
            log.info(f"frame with frame_id: {result.object_name} is saved")
        else:
            log.info(f"failed to save frame with frame_id: {frm_obj_name}")

        return frm_obj_name

    def get_frame_by_frame_id(self, frame_id: str) -> npt.ArrayLike:
        bucket_name = IMAGE_BUCKET_NAME
        frm_obj_name = frame_id

        response: urllib3.HTTPResponse = self.client.get_object(
            bucket_name=bucket_name,
            object_name=frm_obj_name
        )

        frame: npt.ArrayLike = np.frombuffer(response.read())
        if frame is not None:
            log.info(
                f"frame with frame_id: {frame_id} is retrived from storage")

        response.close()
        response.release_conn()

        return frame

    def clear_after_event(self, event: Event):
        b_name = IMAGE_BUCKET_NAME
        prefix = event.request_uuid

        for obj in self.client.list_objects(
                bucket_name=b_name,
                prefix=prefix,
                recursive=True):
            self.client.remove_object(obj.bucket_name, obj.object_name)
        log.info(f"db is cleared after event {event.request_uuid}")
