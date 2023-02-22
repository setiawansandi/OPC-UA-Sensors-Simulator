echo ON
echo start

rem change environment + start the server
call "C:\Users\ASUS\anaconda3\Scripts\activate.bat" "C:\Users\ASUS\anaconda3\envs\opcua"

rem add in the token
call set INFLUX_TOKEN = 'API token copied from InfluxDB cloud'

rem change this to the project directory
call cd D:\github\OPC-UA-SENSORS-SIMULATOR
start python run_opc_server.py

rem start telegraf
start telegraf --config "D:\github\OPC-UA-Sensors-Simulator\telegraf_opcua.conf"