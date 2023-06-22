from __future__ import annotations
from typing import TYPE_CHECKING

from mqtransport import SQSApp

# agent
from .agent import MC_NewCrash

# api-gateway
from .api_gateway import MP_UniqueCrashFound, MP_DuplicateCrashFound

from crash_analyzer.app.message_queue.state import MQAppState

if TYPE_CHECKING:
    from crash_analyzer.app.settings import AppSettings
    from mqtransport import MQApp


class Producers:
    unique_crash: MP_UniqueCrashFound
    duplicated_crash: MP_DuplicateCrashFound


class MQAppInitializer:

    _settings: AppSettings
    _app: MQApp

    @property
    def app(self):
        return self._app

    def __init__(self, settings: AppSettings):
        self._settings = settings
        self._app = None

    async def do_init(self):

        self._app = await self._create_mq_app()
        self._app.state = MQAppState()

        try:
            await self._app.ping()
            await self._configure_channels()

        except:
            await self._app.shutdown()
            raise

    async def _create_mq_app(self):

        mq_broker = self._settings.message_queue.broker.lower()
        mq_settings = self._settings.message_queue

        if mq_broker == "sqs":
            return await SQSApp.create(
                mq_settings.username,
                mq_settings.password,
                mq_settings.region,
                mq_settings.url,
            )

        raise ValueError(f"Unsupported message broker: {mq_broker}")

    async def _create_own_channel(self):
        queues = self._settings.message_queue.queues
        ich = await self._app.create_consuming_channel(queues.crash_analyzer)
        dlq = await self._app.create_producing_channel(queues.dlq)
        ich.use_dead_letter_queue(dlq)
        self._in_channel = ich

    async def _create_other_channels(self):
        queues = self._settings.message_queue.queues
        self._och_api_gateway = await self._app.create_producing_channel(queues.api_gateway)

    def _setup_api_gateway_communication(self, producers: Producers):

        ich = self._in_channel
        och = self._och_api_gateway

        # Incoming messages
        # nop

        # Outcoming messages
        producers.unique_crash = MP_UniqueCrashFound()
        producers.duplicated_crash = MP_DuplicateCrashFound()

        och.add_producer(producers.unique_crash)
        och.add_producer(producers.duplicated_crash)

    def _setup_agent_communication(self, producers: Producers):

        ich = self._in_channel
        #och = self._och_agent

        # Incoming messages
        ich.add_consumer(MC_NewCrash())

        # Outcoming messages
        # nop

    async def _configure_channels(self):
        await self._create_own_channel()
        await self._create_other_channels()

        state: MQAppState = self.app.state
        state.producers = Producers()

        self._setup_api_gateway_communication(state.producers)
        self._setup_agent_communication(state.producers)


async def mq_init(settings: AppSettings):
    initializer = MQAppInitializer(settings)
    await initializer.do_init()
    return initializer.app
