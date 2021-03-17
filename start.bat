@echo off
TITLE Saitama Robot
:: Enables virtual env mode and then starts hannah
env\scripts\activate.bat && py -m MissHannahRobot
