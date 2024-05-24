"""
Agent documentation goes here.
"""

__docformat__ = 'reStructuredText'

import logging
import sys
from volttron.platform.agent import utils
from volttron.platform.vip.agent import Agent, Core, RPC
sys.path.insert(0,'/code/volttron/EMSAgents/loadPriorityController/LPCCAgentv2/lPCCAgnetv2/lpc')
from diagonstic import DiagnosticsSource
from devices import WeMoPlugDevice
from LPC import LPCWeMo
from service import WeMoService
_log = logging.getLogger(__name__)
utils.setup_logging()
__version__ = "0.1"


def lPCCAgnetv2(config_path, **kwargs):
    """
    Parses the Agent configuration and returns an instance of
    the agent created using that configuration.

    :param config_path: Path to a configuration file.
    :type config_path: str
    :returns: Lpccagnetv2
    :rtype: Lpccagnetv2
    """
    try:
        config = utils.load_config(config_path)
    except Exception:
        config = {}

    if not config:
        _log.info("Using Agent defaults for starting configuration.")

    setting1 = int(config.get('setting1', 1))
    setting2 = config.get('setting2', "some/random/topic")

    return Lpccagnetv2(setting1, setting2, **kwargs)


class Lpccagnetv2(Agent,LPCWeMo,DiagnosticsSource,WeMoPlugDevice,WeMoService):
    """
    Document agent constructor here.
    """

    def __init__(self, setting1=1, setting2="some/random/topic", setting7={"CSV_path":"/home/pi/volttron/loadPriorityController/LPCCAgentv2/Building_Config.csv"}, **kwargs):
        super(Lpccagnetv2, self).__init__(**kwargs)
        _log.debug("vip_identity: " + self.core.identity)

        self.setting1 = setting1
        self.setting2 = setting2
        self.setting7 = setting7

        self.default_config = {"setting1": setting1,
                               "setting2": setting2,
                               "setting7": setting7}

        #self.Wemodevices=WeMoPlugDevice()
        self.WeMoplugservice=WeMoService()
        self.WeMoLPCmodule=LPCWeMo(self.vip)
        self.WeModevices=WeMoPlugDevice(self.vip)
        #self.WeMoplugservice.register_devices(self.setting7["CSV_path"],self.WeMoLPCmodule,self.WeModevices)
        self.core.periodic(2,self.dowork)
        # Set a default configuration to ensure that self.configure is called immediately to setup
        # the agent.
        self.vip.config.set_default("config", self.default_config)
        # Hook self.configure up to changes to the configuration file "config".
        self.vip.config.subscribe(self.configure, actions=["NEW", "UPDATE"], pattern="config")
        #self.WeMoplugservice.register_devices(self.setting7["CSV_path"],self.WeMoLPCmodule,self.WeModevices)
    def configure(self, config_name, action, contents):
        """
        Called after the Agent has connected to the message bus. If a configuration exists at startup
        this will be called before onstart.

        Is called every time the configuration in the store changes.
        """
        config = self.default_config.copy()
        config.update(contents)

        _log.debug("Configuring Agent")

        try:
            setting1 = int(config["setting1"])
            setting2 = str(config["setting2"])
            setting7 = config["setting7"]
        except ValueError as e:
            _log.error("ERROR PROCESSING CONFIGURATION: {}".format(e))
            return

        self.setting1 = setting1
        self.setting2 = setting2
        self.setting7 = setting7

        for x in self.setting2:
            self._create_subscriptions(str(x))
            
        self.vip.pubsub.subscribe(peer='pubsub',prefix='Wemo_Schedule',callback=self._handle_publish)

    def _create_subscriptions(self, topic):
        """
        Unsubscribe from all pub/sub topics and create a subscription to a topic in the configuration which triggers
        the _handle_publish callback
        """
        self.vip.pubsub.unsubscribe("pubsub", None, None)

        self.vip.pubsub.subscribe(peer='pubsub',
                                  prefix=topic,
                                  callback=self._handle_publish,all_platforms=True)

    def _handle_publish(self, peer, sender, bus, topic, headers, message):
        """
        Callback triggered by the subscription setup using the topic from the agent's config file
        """
        #self.Wemodevices.connect()
        self.WeMoplugservice.device_status_update(topic,message,self.WeMoLPCmodule)
        self.WeMoplugservice.device_set_control_mode(topic,message,self.WeMoLPCmodule,self.WeModevices)

        print("Handle publish")

    @Core.receiver("onstart")
    def onstart(self, sender, **kwargs):
        """
        This is method is called once the Agent has successfully connected to the platform.
        This is a good place to setup subscriptions if they are not dynamic or
        do any other startup activities that require a connection to the message bus.
        Called after any configurations methods that are called at startup.

        Usually not needed if using the configuration store.
        """
        # Example publish to pubsub
        self.vip.pubsub.publish('pubsub', "some/random/topic", message="HI!")
        self.WeMoplugservice.register_devices(self.setting7["CSV_path"],self.WeMoLPCmodule,self.WeModevices)
        # Example RPC call
        # self.vip.rpc.call("some_agent", "some_method", arg1, arg2)
        #pass

    @Core.receiver("onstop")
    def onstop(self, sender, **kwargs):
        """
        This method is called when the Agent is about to shutdown, but before it disconnects from
        the message bus.
        """
        pass

    @RPC.export
    def rpc_method(self, arg1, arg2, kwarg1=None, kwarg2=None):
        """
        RPC method

        May be called from another agent via self.core.rpc.call
        """
        return self.setting1 + arg1 - arg2

    def dowork(self):
        print('Total WeMo Consumpiton: ',self.WeMoLPCmodule.get_total_device_consumption())

def main():
    """Main method called to start the agent."""
    utils.vip_main(lPCCAgnetv2, 
                   version=__version__)


if __name__ == '__main__':
    # Entry point for script
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        pass
