@echo off
echo Starting update...
ping 127.0.0.1 -n 5 > nul
xcopy /s /y "%~dp0new_files\*" "%~dp0"
rmdir /s /q "%~dp0new_files"
start "" "%~dp0JournalTrade.exe"
exit