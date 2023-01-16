import asyncio
import logging
import numpy as np
import pickle

from asyncua import Server, ua
from asyncua.common.methods import uamethod

# Initialization
TOTAL_GATEWAY = 2
TOTAL_NODE = 3 # no. of node in each gateway
GW_LIST = np.empty(TOTAL_GATEWAY, dtype=object) # store gateway objs
NODE_LIST = np.empty([TOTAL_GATEWAY, TOTAL_NODE], dtype=object) # store node(sensor) objs
NODE_VALUE = None # contains pointer to SURS_DATA
SURS_CLASS = None
SURS_DATA = None # surrogate data


def load_pkl():
    with open("data/surs.pkl", "rb") as f:
        surs_obj = pickle.load(f)

    SURS_CLASS = surs_obj['sursclass']
    SURS_CLASS = np.array(SURS_CLASS) #; sursclass = sursclass[:, np.newaxis] 
    SURS_DATA = surs_obj['sursdata']

    del surs_obj # to free up memory


@uamethod
def func(parent, value):
    return value * 2


async def main():
    _logger = logging.getLogger(__name__)
    load_pkl()

    # setup server
    server = Server()
    await server.init()
    server.set_endpoint("opc.tcp://0.0.0.0:4840/opcua/server/")
    server.set_server_name("OPC-UA Simulation Server")


    # set up our own namespace, not really necessary but should as spec
    uri = "http://sensors.opcua.sp.edu.sg"
    idx = await server.register_namespace(uri)


    # populating our address space
    # First a folder to organise our nodes
    data_sources = await server.nodes.objects.add_folder(idx, "DataSources")

    # server.nodes, contains links to very common nodes like objects and root
    for n_gw in range(TOTAL_GATEWAY):
        GW_LIST[n_gw] = await data_sources.add_folder(idx, f"Gateway {n_gw}")
        for n_node in range(TOTAL_NODE):
            NODE_LIST[n_gw][n_node] = await GW_LIST[n_gw].add_variable(idx, f"G{n_gw}_Sensor_{n_node}", 0.1)
            # Set variable to be writable by clients
            # await myvar.set_writable()
    
    # server status
    await server.nodes.objects.add_method(
        ua.NodeId("ServerMethod", idx),
        ua.QualifiedName("ServerMethod", idx),
        func,
        [ua.VariantType.Int64],
        [ua.VariantType.Int64],
    )


    _logger.info("Starting server!")
    async with server:
        while True:
            await asyncio.sleep(1)
            new_val = await NODE_LIST[0][0].get_value() + 0.1
            _logger.info("Set value of %s to %.1f", NODE_LIST[0][0], new_val)
            await NODE_LIST[0][0].write_value(new_val)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    asyncio.run(main(), debug=True)