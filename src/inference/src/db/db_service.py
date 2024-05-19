import os
import pickle
import uuid
import pathlib
import urllib3
from io import BytesIO

import numpy as np
import numpy.typing as npt
from dotenv import load_dotenv, find_dotenv
import redis
from minio import Minio
from minio import S3Error

from inference_models import Event
from logger import log

_env_file = find_dotenv(f'./.{os.getenv("ENV", "dev")}.env')
load_dotenv(_env_file)


class PredCacheDatabase():
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

    def save_pred(self, event: Event, predicitons: list[str]):
        for pred in predicitons:
            fine_pred = " " + str(pred)
            self.conn.append(event.request_uuid, fine_pred)

    def is_exists(self, event: Event):
        return self.conn.keys(event.request_uuid)

    def clear_after_event(self, event: Event):
        cursor = '0'
        ns_keys = event.request_uuid + '*'
        while cursor != 0:
            cursor, keys = self.conn.scan(
                cursor=cursor, match=ns_keys, count=10_000)
            if keys:
                self.conn.delete(*keys)


IMAGE_BUCKET_NAME = "frames-for-inference"


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
        self.__init_bucket()

    def __init_bucket(self):
        if not self.client.bucket_exists(IMAGE_BUCKET_NAME):
            self.client.make_bucket(IMAGE_BUCKET_NAME)

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

    def get_frame_by_frame_id(self, frame_id: str) -> npt.ArrayLike:
        bucket_name = IMAGE_BUCKET_NAME
        frm_obj_name = frame_id
        frame = None
        try:
            response: urllib3.HTTPResponse = self.client.get_object(
                bucket_name=bucket_name,
                object_name=frm_obj_name
            )

            raw_shape = response.headers["x-amz-meta-shape"]
            shape = tuple(map(int, raw_shape.split(",")))

            frame: npt.ArrayLike = pickle.loads(response.read()).reshape(shape)

            log.info(
                f"frame with frame_id: {frame_id} is retrived from storage")
        except S3Error:
            log.info(f"image not found in storage: {frame_id}")
        finally:
            response.close()
            response.release_conn()

        return frame
