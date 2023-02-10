import asyncio
import logging
import numpy as np
import pickle
import random

from asyncua import Server, ua
from asyncua.common.methods import uamethod

from utils.Node import Node

# Initialization
OUTPUT_INTERVAL = 1 # Delay between each packet in second
TOTAL_GATEWAY = 2 # no.of simulated gateway
TOTAL_NODE = 100 # no. of node in each gateway (wihart 1410s supports up to 200 only)

GW_LIST = [] # stores gateway objs
NODE_LIST = [] # stores node(sensor) objs

SURS_CLASS = None # stores surrogate class
SURS_DATA = None # stores surrogate data


def load_surs_from_pkl(filename=None):
    with open(filename, "rb") as f:
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
    load_surs_from_pkl(filename="data/temperature.pkl")


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
            
            # initialise node
            node = await GW_LIST[n_gw].add_object(idx, f"Temperature {n_node}")

            # << Node's variables, are values transmitted by sensor >>
            # randomly select data from the surrogate data pool; rand_n=index
            rand_n = random.randint(0, len(SURS_DATA)-1)

            # get score and value of the first element
            score = SURS_CLASS[rand_n]
            value = str(SURS_DATA[rand_n][0][0])
            # ^^[rand_n] = surr index; [0] = 1st row; [0] = 1st col (remain 0 if there's only 1 col)

            # set the node's id & value
            nodeID = f'ns=2; s=DataSources.sim-wihartgw{n_gw}.Temperature {n_node}.PV' 
            # ^ format: ns=number; s=whatYouWantToCallYourID
            variable = await node.add_variable(nodeID, "PV", value)

            # set variable's properties #TODO append to Node class
            # var_property = []
            # var_property.append(await variable.add_attribute(, "Definition",))

            node_obj = Node(node)
            # add variables, surr pointers, and data score(category)
            node_obj.add_var(variable)
            node_obj.add_surs_ptr(rand_n)
            node_obj.add_score(score)

            # save the node to a list
            NODE_LIST.append(node_obj)

    
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
            await asyncio.sleep(OUTPUT_INTERVAL) # delay between each batch transfer

            for node in NODE_LIST:
                # loop through each element of surrogate data
                # if not the end of array
                if node.surs_index < len(SURS_DATA[node.surs_ptr[0]]): # length of column
                    # print(f'{node.surs_index} - {node.surs_ptr[0]}') # DEBUG
                    new_val = str(SURS_DATA[node.surs_ptr[0]][node.surs_index][0])
                    node.surs_index += 1
                # else select new set of surrogate
                else:
                    # randomly select new set of data from the surrogate data pool; rand_n=index
                    rand_n = random.randint(0, len(SURS_DATA)-1)
                    # get score and value of the first element
                    score = SURS_CLASS[rand_n]
                    value = str(SURS_DATA[rand_n][0][0])

                    # add variables, surr pointers, and data score(category)
                    node.update_surs_ptr(index=0, ptr=rand_n) # update first element in the list
                    node.update_score(index=0, score=score)

                    new_val = str(SURS_DATA[node.surs_ptr[0]][0][0])
                    node.surs_index = 1

                await node.variables[0].write_value(new_val)



if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    asyncio.run(main(), debug=True)
    