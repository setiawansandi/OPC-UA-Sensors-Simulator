echo ON
echo start

rem change environment + start the server
call "C:\Users\ASUS\anaconda3\Scripts\activate.bat" "C:\Users\ASUS\anaconda3\envs\opcua"
call cd D:\github\OPC-UA-SENSORS-SIMULATOR
start python run_opc_server.py

rem link to cloud database (InfluxDB Cloud)
start telegraf --config "D:\github\OPC-UA-Sensors-Simulator\telegraf_opcua.conf"