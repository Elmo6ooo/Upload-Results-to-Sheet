import gspread
from oauth2client.service_account import ServiceAccountCredentials
from gspread.cell import Cell

'''
result = "";
for (i = 0; i < document.getElementsByClassName('file-path-right-ellipsized ng-star-inserted').length; i++) {
	S = document.getElementsByClassName('target-status')[i+1].textContent;
	if (S.includes('Tool Failed'))
	   S = "Tool_Fail";
	result += document.getElementsByClassName('file-path-right-ellipsized ng-star-inserted')[i].textContent.replace('arm64-v8a ','')+" "+S+" "
}
'''

scopes = ["https://spreadsheets.google.com/feeds"]
credentials = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scopes)
client = gspread.authorize(credentials)
sheet = client.open_by_key("1eSp4g_2Z86MnZLUVljhMoDt1OgRIPeEV0KYMVq22zag").worksheet("UDC-SH-CTS-Auto")	

#read file 
result = []
file = open('result.txt','r')
lines = file.read().splitlines()
lines[0] = lines[0].replace("'", "")

for line in lines:
	result.extend(line.split())

#keeps data that we want to upload
cells = []

# clear result column
sheet.batch_clear(['C:C'])

#col in dict
dic = {}
col = sheet.col_values(2)
for i in range(3):
	col.pop(0)
index = 4
for i in col:
	dic[i] = index
	cells.append(Cell(dic[i], 3, 'Not Found'))
	index = index + 1

#0:Module, 1:Status
for i in range(len(result)-1, 0, -2):
	if "[instant]" in result[i-1]:
		result[i-1] = result[i-1].replace("[instant]", "")
	elif "[run-on-secondary-user]" in result[i-1]:
		result[i-1] = result[i-1].replace("[run-on-secondary-user]", "")
	elif "[run-on-work-profile]" in result[i-1]:
		result[i-1] = result[i-1].replace("[run-on-work-profile]", "")
	#data to upload
	if result[i-1] in dic:
		if "Passed" in result[i]:
			result[i] =  "Auto PASS"
		elif "Failed" in result[i]:
			result[i] = "Auto FAIL"
		elif "Skipped" in result[i]:
			result[i] = "Skipped"
		elif "Tool_Fail" in result[i]:
			result[i] = "Tool_Fail"
		elif "Unspecified" in result[i]:
			result[i] = "Unspecified"

		cells.append(Cell(dic[result[i-1]], 3, result[i]))
	
	else:
		print("Not found: %s" %result[i-1])
		
#upload data	
sheet.update_cells(cells)

print("DONE")	