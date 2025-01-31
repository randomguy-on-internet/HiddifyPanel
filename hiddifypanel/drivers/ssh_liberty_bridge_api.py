from .abstract_driver import DriverABS
from hiddifypanel.models import *
import redis

USERS_SET = "ssh-server:users"
USERS_USAGE = "ssh-server:users-usage"


class SSHLibertyBridgeApi(DriverABS):

    def get_ssh_redis_client(self):
        if not hasattr(self, 'redis_client'):
            self.redis_client = redis.from_url(hconfig(ConfigEnum.ssh_server_redis_url), decode_responses=True)

        return self.redis_client

    def get_enabled_users(self):
        if hconfig(ConfigEnum.is_parent):
            return
        redis_client = self.get_ssh_redis_client()
        members = redis_client.smembers(USERS_SET)
        return {m.split("::")[0]: 1 for m in members}

    def add_client(self, user):
        if hconfig(ConfigEnum.is_parent):
            return
        print(f'Adding SSH {user}')
        redis_client = self.get_ssh_redis_client()
        redis_client.sadd(USERS_SET, f'{user.uuid}::{user.ed25519_public_key}')
        redis_client.save()

    def remove_client(self, user):
        if hconfig(ConfigEnum.is_parent):
            return
        redis_client = self.get_ssh_redis_client()
        redis_client.srem(USERS_SET, f'{user.uuid}::{user.ed25519_public_key}')
        redis_client.hdel(USERS_USAGE, f'{user.uuid}')
        redis_client.save()

    def get_usage(self, client_uuid: str, reset: bool = True) -> int:
        if hconfig(ConfigEnum.is_parent):
            return
        redis_client = self.get_ssh_redis_client()
        value = redis_client.hget(USERS_USAGE, client_uuid)

        if value is None:
            return 0

        value = int(value)

        if reset:
            redis_client.hincrby(USERS_USAGE, client_uuid, -value)
            redis_client.save()
        print(f'ssh usage {client_uuid} {value}')
        return value
