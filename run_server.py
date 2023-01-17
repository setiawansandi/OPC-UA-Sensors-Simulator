import asyncio
import logging
import numpy as np
import pickle
import random

from asyncua import Server, ua
from asyncua.common.methods import uamethod

from Node import Node

# Initialization
TOTAL_GATEWAY = 2
TOTAL_NODE = 3 # no. of node in each gateway
GW_LIST = [] # store gateway objs
NODE_LIST = [] # store node(sensor) objs
SURS_CLASS = None # surrogate class
SURS_DATA = None # surrogate data


def load_surs_from_pkl():
    with open("data/surs.pkl", "rb") as f:
        surs_obj = pickle.load(f)

    global SURS_CLASS, SURS_DATA # indicate vars are global

    SURS_CLASS = surs_obj['sursclass']
    SURS_CLASS = np.array(SURS_CLASS) #; sursclass = sursclass[:, np.newaxis]
    SURS_DATA = surs_obj['sursdata']

    del surs_obj # to free up memory


@uamethod
def func(parent, value):
    return value * 2


async def main():
    _logger = logging.getLogger(__name__)

    # v==================== Load Surrogate Data =====================v
    load_surs_from_pkl()


    # v======================== Setup Server ========================v

    server = Server()
    await server.init()
    server.set_endpoint("opc.tcp://0.0.0.0:4840/opcua/server/")
    server.set_server_name("OPC-UA Simulation Server")

    # set up our own namespace, not really necessary but should as spec
    uri = "http://sensors.opcua.sp.edu.sg"
    idx = await server.register_namespace(uri)


    # v=================== Populating AddressSpace ==================v

    # << folder to organise our nodes >>
    data_sources = await server.nodes.objects.add_folder(idx, "DataSources")

    # << WirelessHart folder, contains links to sensor nodes >>
    for n_gw in range(TOTAL_GATEWAY):
        GW_LIST.append(await data_sources.add_folder(idx, f"sim-wihartgw{n_gw}"))

        # << Sensor nodes (object), simulating sensor devices >>
        for n_node in range(TOTAL_NODE):
            # Node is a defined class that mimics typical sensor data structure
            node = Node(await GW_LIST[n_gw].add_object(idx, f"Temperature {n_node}"))

            # << Node's variables, are values transmitted by sensor >>
            # randomly select data from the surrogate data pool; n=index
            n = random.randint(0, len(SURS_DATA)-1)

            # get score and value of the first element
            score = SURS_CLASS[n]
            value = str(SURS_DATA[n][0][0])
            # ^^[n] = which surr; [0] = 1st row; [0] = 1st col (remain 0 if there's only 1 col)

            # set the node id & value
            nodeID = f'ns=2; s=DataSources.sim-wihartgw{n_gw}.Temperature {n_node}.PV' #"ns=number; s=whatYouWantToCallYourID"
            variable = await node.node_obj.add_variable(nodeID, "PV", value)

            # add variables, surr pointers, and data score(category)
            node.add_var(variable)
            node.add_surs_ptr(n)
            node.add_score(score)

            # save the node to a list
            NODE_LIST.append(node)

    
    # << Server object >>
    await server.nodes.objects.add_method(
        ua.NodeId("ServerMethod", idx),
        ua.QualifiedName("ServerMethod", idx),
        func,
        [ua.VariantType.Int64],
        [ua.VariantType.Int64],
    )


    # v======================== Start Server ========================v

    _logger.info("Starting server!")
    async with server:
        while True:
            await asyncio.sleep(1)
            for node in NODE_LIST:
                # _logger.info("Set value of %s to %.1f", NODE_LIST[0][0], new_val)
                #await NODE_LIST[0][0].write_value(new_val)
                pass
            # new_val = await NODE_LIST[0][0].get_value() + 0.1
            # _logger.info("Set value of %s to %.1f", NODE_LIST[0][0], new_val)
            # await NODE_LIST[0][0].write_value(new_val)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    asyncio.run(main(), debug=True)